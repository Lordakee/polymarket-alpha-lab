from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime, timedelta, timezone
import hashlib
import json
import re

import pytest

from polymarket_alpha_lab.paper_autonomous_readiness_digest import (
    NEXT_REVIEW_ACTION_BY_STATUS,
    PASS_REASON_CODE,
    PaperAutonomousReadinessDigestEvidence,
    PaperAutonomousReadinessDigestReasonCodeCount,
    PaperAutonomousReadinessDigestReport,
)


GENERATED_AT = datetime(2026, 6, 29, 12, 0, tzinfo=UTC)
SOURCE_TZ = timezone(timedelta(hours=-4))
SOURCE_GENERATED_AT = datetime(2026, 6, 29, 8, 0, tzinfo=SOURCE_TZ)
CONFIG_VERSION = "paper-autonomous-readiness-digest-test-v0"
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def _codec_module():
    import polymarket_alpha_lab.paper_autonomous_readiness_digest_db_row as codec

    return codec


def _evidence(
    source_name: str,
    status: str,
    *,
    required: bool,
) -> PaperAutonomousReadinessDigestEvidence:
    return PaperAutonomousReadinessDigestEvidence(
        source_name=source_name,
        status=status,
        recommended_next_step=f"review_{source_name}_{status}",
        generated_at=SOURCE_GENERATED_AT,
        config_version=f"{source_name}-config-v0",
        reason_codes=(f"{source_name}_{status}",),
        required=required,
    )


def _reason_count(reason_code: str, count: int = 1) -> PaperAutonomousReadinessDigestReasonCodeCount:
    return PaperAutonomousReadinessDigestReasonCodeCount(reason_code, count)


def _report(
    *,
    config_version: str = CONFIG_VERSION,
    digest_status: str = "watch",
    evidence: tuple[PaperAutonomousReadinessDigestEvidence, ...] | None = None,
    reason_codes: tuple[str, ...] = (
        "readiness_gate_pass",
        "screening_watch",
    ),
) -> PaperAutonomousReadinessDigestReport:
    if evidence is None:
        evidence = (
            _evidence("readiness_gate", "pass", required=True),
            _evidence("screening", "watch", required=False),
        )
    return PaperAutonomousReadinessDigestReport(
        generated_at=GENERATED_AT,
        config_version=config_version,
        digest_status=digest_status,
        recommended_next_review_action=NEXT_REVIEW_ACTION_BY_STATUS[digest_status],
        evidence=evidence,
        source_config_versions=tuple(
            (row.source_name, row.config_version) for row in evidence
        ),
        reason_code_counts=tuple(_reason_count(reason_code) for reason_code in reason_codes),
        reason_codes=reason_codes,
    )


def _status_report(digest_status: str) -> PaperAutonomousReadinessDigestReport:
    if digest_status == "pass":
        evidence = (_evidence("readiness_gate", "pass", required=True),)
        reason_codes = (PASS_REASON_CODE, "readiness_gate_pass")
    elif digest_status == "watch":
        evidence = (
            _evidence("readiness_gate", "pass", required=True),
            _evidence("screening", "watch", required=False),
        )
        reason_codes = ("readiness_gate_pass", "screening_watch")
    elif digest_status == "blocked":
        evidence = (
            _evidence("readiness_gate", "blocked", required=True),
        )
        reason_codes = ("readiness_gate_blocked",)
    else:
        raise AssertionError(f"unexpected digest_status {digest_status}")
    return _report(
        digest_status=digest_status,
        evidence=evidence,
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
        pytest.fail("digest DB JSON contains floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_digest_db_row_serializes_payload_and_round_trips() -> None:
    codec = _codec_module()
    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperAutonomousReadinessDigestDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == CONFIG_VERSION
    assert row.digest_status == "watch"
    assert row.recommended_next_review_action == (
        "review_watch_paper_autonomous_readiness_evidence"
    )
    assert row.evidence_json == [
        {
            "source_name": "readiness_gate",
            "status": "pass",
            "recommended_next_step": "review_readiness_gate_pass",
            "generated_at": "2026-06-29T12:00:00+00:00",
            "config_version": "readiness_gate-config-v0",
            "reason_codes": ["readiness_gate_pass"],
            "required": True,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "source_name": "screening",
            "status": "watch",
            "recommended_next_step": "review_screening_watch",
            "generated_at": "2026-06-29T12:00:00+00:00",
            "config_version": "screening-config-v0",
            "reason_codes": ["screening_watch"],
            "required": False,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.source_config_versions_json == [
        ["readiness_gate", "readiness_gate-config-v0"],
        ["screening", "screening-config-v0"],
    ]
    assert row.reason_code_counts_json == [
        {
            "reason_code": "readiness_gate_pass",
            "report_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
        {
            "reason_code": "screening_watch",
            "report_count": 1,
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert row.reason_codes_json == ["readiness_gate_pass", "screening_watch"]
    assert row.payload_json["evidence"] == row.evidence_json
    assert row.payload_json["source_config_versions"] == row.source_config_versions_json
    assert row.payload_json["reason_code_counts"] == row.reason_code_counts_json
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_no_floats(row.evidence_json)
    _assert_no_floats(row.source_config_versions_json)
    _assert_no_floats(row.reason_code_counts_json)
    _assert_no_floats(row.reason_codes_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_autonomous_readiness_digest_report_to_db_row(report) == row
    assert codec.paper_autonomous_readiness_digest_report_from_db_row(row) == report
    assert codec.paper_autonomous_readiness_digest_to_db_row(report) == row
    assert codec.paper_autonomous_readiness_digest_from_db_row(row) == report


def test_digest_db_row_round_trips_selection_summary_trend_gate_source() -> None:
    codec = _codec_module()
    evidence = (
        _evidence("readiness_gate", "pass", required=True),
        _evidence("agreement_trend_gate", "pass", required=False),
        _evidence("selection_summary_trend_gate", "blocked", required=False),
        _evidence("ledger", "pass", required=False),
    )
    reason_codes = (
        "agreement_trend_gate_pass",
        "ledger_pass",
        "readiness_gate_pass",
        "selection_summary_trend_gate_blocked",
    )
    report = _report(
        digest_status="blocked",
        evidence=evidence,
        reason_codes=reason_codes,
    )

    row = codec.to_db_row(report)

    assert [item["source_name"] for item in row.evidence_json] == [
        "readiness_gate",
        "agreement_trend_gate",
        "selection_summary_trend_gate",
        "ledger",
    ]
    assert row.source_config_versions_json == [
        ["readiness_gate", "readiness_gate-config-v0"],
        ["agreement_trend_gate", "agreement_trend_gate-config-v0"],
        [
            "selection_summary_trend_gate",
            "selection_summary_trend_gate-config-v0",
        ],
        ["ledger", "ledger-config-v0"],
    ]
    assert row.reason_codes_json == list(reason_codes)
    _assert_no_floats(row.payload_json)
    assert codec.from_db_row(row) == report


@pytest.mark.parametrize("digest_status", ("pass", "watch", "blocked"))
def test_digest_db_row_round_trips_every_source_of_truth_action(
    digest_status: str,
) -> None:
    codec = _codec_module()
    report = _status_report(digest_status)

    row = codec.to_db_row(report)

    assert row.digest_status == digest_status
    assert row.recommended_next_review_action == (
        NEXT_REVIEW_ACTION_BY_STATUS[digest_status]
    )
    assert codec.from_db_row(row) == report


def test_digest_db_row_hash_is_deterministic_and_uses_full_payload() -> None:
    codec = _codec_module()
    report = _report()
    same_report = PaperAutonomousReadinessDigestReport(**report.__dict__)
    changed_report = _report(config_version="paper-autonomous-readiness-digest-test-v1")

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(changed_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_digest_db_row_is_frozen() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_digest_db_row_rejects_wrong_report_and_row_types() -> None:
    codec = _codec_module()

    with pytest.raises(ValueError, match="PaperAutonomousReadinessDigestReport"):
        codec.to_db_row(object())

    with pytest.raises(ValueError, match="PaperAutonomousReadinessDigestDbRow"):
        codec.from_db_row(object())


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_digest_db_row_rejects_false_report_flags_before_write(flag_name: str) -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_digest_db_row_rejects_false_nested_evidence_flags() -> None:
    codec = _codec_module()
    report = _report()
    object.__setattr__(report.evidence[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_digest_db_row_rejects_corrupted_stored_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "evidence": [
            {**row.payload_json["evidence"][0], "paper_only": False},
            *row.payload_json["evidence"][1:],
        ],
    }

    with pytest.raises(ValueError, match="paper_only"):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
                "evidence_json": payload["evidence"],
            },
        )


def test_digest_from_db_row_rejects_bypassed_corrupted_payload_flags() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "evidence": [
            {**row.payload_json["evidence"][0], "paper_only": False},
            *row.payload_json["evidence"][1:],
        ],
    }
    malformed = object.__new__(codec.PaperAutonomousReadinessDigestDbRow)
    for key, value in {
        **_row_values(row),
        "report_sha256": _canonical_payload_sha256(payload),
        "payload_json": payload,
        "evidence_json": payload["evidence"],
    }.items():
        object.__setattr__(malformed, key, value)

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)


def test_digest_db_row_rejects_payload_hash_mismatch_before_read() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {**row.payload_json, "paper_only": False}

    with pytest.raises(ValueError, match="report_sha256"):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{**_row_values(row), "payload_json": payload},
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_digest_db_row_rejects_payload_flag_mismatches_before_read(
    flag_name: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())
    payload = {**row.payload_json, flag_name: False}

    with pytest.raises(ValueError, match=flag_name):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_digest_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="evidence_json"):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{
                **_row_values(row),
                "evidence_json": [{**row.evidence_json[0], "bad_float": 1.0}],
            },
        )
    with pytest.raises(ValueError, match="source_config_versions_json"):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{
                **_row_values(row),
                "source_config_versions_json": [["readiness_gate", 1.0]],
            },
        )
    with pytest.raises(ValueError, match="reason_code_counts_json"):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{
                **_row_values(row),
                "reason_code_counts_json": [
                    {**row.reason_code_counts_json[0], "report_count": 1.0},
                ],
            },
        )
    with pytest.raises(ValueError, match="payload_json"):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{**_row_values(row), "payload_json": {**row.payload_json, "bad": 0.1}},
        )


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 29, 12, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "paper-autonomous-readiness-digest-test-v1"}, "config_version"),
        ({"digest_status": "pass"}, "digest_status"),
        (
            {"recommended_next_review_action": "continue_operator_review"},
            "recommended_next_review_action",
        ),
        ({"evidence_json": []}, "evidence_json"),
        ({"source_config_versions_json": []}, "source_config_versions_json"),
        ({"reason_code_counts_json": []}, "reason_code_counts_json"),
        ({"reason_codes_json": ["readiness_gate_pass"]}, "reason_codes_json"),
    ),
)
def test_digest_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{**_row_values(row), **overrides},
        )

@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 29, 12, 0)}, "generated_at"),
        ({"config_version": " paper-autonomous-readiness-digest-test-v0"}, "config_version"),
        ({"digest_status": "live"}, "digest_status"),
        ({"evidence_json": "evidence"}, "evidence_json"),
        ({"source_config_versions_json": "versions"}, "source_config_versions_json"),
        ({"reason_code_counts_json": "reasons"}, "reason_code_counts_json"),
        ({"reason_codes_json": [1]}, "reason_codes_json"),
        ({"paper_only": False}, "paper_only"),
        ({"report_only": False}, "report_only"),
        ({"readonly": False}, "readonly"),
    ),
)
def test_digest_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    codec = _codec_module()
    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperAutonomousReadinessDigestDbRow(
            **{**_row_values(row), **overrides},
        )
