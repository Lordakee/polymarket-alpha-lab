from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
from pathlib import Path
import re

import pytest

from polymarket_alpha_lab.paper_project_screening_rank_stability import (
    PaperProjectScreeningRankStabilityReport,
    PaperProjectScreeningRankStabilityRow,
)


GENERATED_AT = datetime(2026, 6, 22, 13, 0, tzinfo=UTC)
LATEST_GENERATED_AT = datetime(2026, 6, 22, 12, 55, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


class ProjectRankStabilityReportSubclass(PaperProjectScreeningRankStabilityReport):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _stable_row() -> PaperProjectScreeningRankStabilityRow:
    return PaperProjectScreeningRankStabilityRow(
        market_slug="alpha",
        stability_status="stable",
        latest_research_bucket="research_ready",
        latest_screening_status="screening_ready",
        latest_source_status="paper_review_ready",
        latest_scoring_side="yes",
        present_snapshot_count=2,
        ready_snapshot_count=2,
        first_rank=1,
        latest_rank=1,
        rank_delta=0,
        max_rank_movement=0,
        first_screening_score=d("0.700000"),
        latest_screening_score=d("0.720000"),
        screening_score_delta=d("0.020000"),
        max_screening_score_delta=d("0.020000"),
        scoring_side_changed=False,
        source_status_changed=False,
        screening_status_changed=False,
        research_bucket_changed=False,
        reason_codes=("stable_research_ready",),
    )


def _watch_row() -> PaperProjectScreeningRankStabilityRow:
    return PaperProjectScreeningRankStabilityRow(
        market_slug="beta",
        stability_status="watch",
        latest_research_bucket="research_ready",
        latest_screening_status="screening_ready",
        latest_source_status="paper_review_ready",
        latest_scoring_side="no",
        present_snapshot_count=2,
        ready_snapshot_count=2,
        first_rank=2,
        latest_rank=2,
        rank_delta=0,
        max_rank_movement=0,
        first_screening_score=d("0.500000"),
        latest_screening_score=d("0.510000"),
        screening_score_delta=d("0.010000"),
        max_screening_score_delta=d("0.010000"),
        scoring_side_changed=True,
        source_status_changed=False,
        screening_status_changed=False,
        research_bucket_changed=False,
        reason_codes=("scoring_side_changed",),
    )


def _report() -> PaperProjectScreeningRankStabilityReport:
    rows = (_stable_row(), _watch_row())
    return PaperProjectScreeningRankStabilityReport(
        generated_at=GENERATED_AT,
        config_version="project-screening-rank-stability-v0",
        source_report_count=2,
        candidate_count=2,
        stability_status="watch",
        stable_count=1,
        watch_count=1,
        blocked_count=0,
        stable_ready_count=1,
        unstable_ready_count=1,
        scoring_side_changed_count=1,
        source_status_changed_count=0,
        screening_status_changed_count=0,
        research_bucket_changed_count=0,
        latest_generated_at=LATEST_GENERATED_AT,
        top_stable_market_slug="alpha",
        reason_codes=("unstable_ready_candidates_present",),
        rows=rows,
    )


def _empty_report() -> PaperProjectScreeningRankStabilityReport:
    return PaperProjectScreeningRankStabilityReport(
        generated_at=GENERATED_AT,
        config_version="project-screening-rank-stability-v0",
        source_report_count=0,
        candidate_count=0,
        stability_status="watch",
        stable_count=0,
        watch_count=0,
        blocked_count=0,
        stable_ready_count=0,
        unstable_ready_count=0,
        scoring_side_changed_count=0,
        source_status_changed_count=0,
        screening_status_changed_count=0,
        research_bucket_changed_count=0,
        latest_generated_at=None,
        top_stable_market_slug=None,
        reason_codes=("no_latest_candidates",),
        rows=(),
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
        pytest.fail("project screening rank stability DB JSON must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_no_floats(item)


def test_project_rank_stability_db_row_serializes_payload_and_round_trips() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    report = _report()

    row = codec.to_db_row(report)

    assert type(row) is codec.PaperProjectScreeningRankStabilityDbRow
    assert SHA256_RE.fullmatch(row.report_sha256)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "project-screening-rank-stability-v0"
    assert row.stability_status == "watch"
    assert row.reason_codes_json == ["unstable_ready_candidates_present"]
    assert row.source_report_count == 2
    assert row.candidate_count == 2
    assert row.stable_count == 1
    assert row.watch_count == 1
    assert row.blocked_count == 0
    assert row.stable_ready_count == 1
    assert row.unstable_ready_count == 1
    assert row.scoring_side_changed_count == 1
    assert row.source_status_changed_count == 0
    assert row.screening_status_changed_count == 0
    assert row.research_bucket_changed_count == 0
    assert row.latest_generated_at == LATEST_GENERATED_AT
    assert row.top_stable_market_slug == "alpha"
    assert row.rows_json == row.payload_json["rows"]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-06-22T13:00:00+00:00"
    assert row.payload_json["latest_generated_at"] == "2026-06-22T12:55:00+00:00"
    assert row.payload_json["rows"][0]["latest_screening_score"] == "0.720000"
    assert row.payload_json["rows"][1]["screening_score_delta"] == "0.010000"
    assert row.payload_json["rows"][1]["max_screening_score_delta"] == "0.010000"
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_no_floats(row.rows_json)
    _assert_no_floats(row.payload_json)

    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert codec.from_db_row(row) == report
    assert codec.paper_project_screening_rank_stability_report_to_db_row(report) == row
    assert codec.paper_project_screening_rank_stability_report_from_db_row(row) == report


def test_project_rank_stability_db_row_hash_is_deterministic() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    report = _report()
    same_report = PaperProjectScreeningRankStabilityReport(**report.__dict__)
    different_report = PaperProjectScreeningRankStabilityReport(
        **{**report.__dict__, "config_version": "project-screening-rank-stability-v1"},
    )

    first = codec.to_db_row(report)
    second = codec.to_db_row(same_report)
    third = codec.to_db_row(different_report)

    assert first.report_sha256 == second.report_sha256
    assert first.payload_json == second.payload_json
    assert first.report_sha256 != third.report_sha256


def test_project_rank_stability_db_row_preserves_empty_report_canonical_state() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    row = codec.to_db_row(_empty_report())

    assert row.candidate_count == 0
    assert row.stable_count == 0
    assert row.watch_count == 0
    assert row.blocked_count == 0
    assert row.stable_ready_count == 0
    assert row.unstable_ready_count == 0
    assert row.scoring_side_changed_count == 0
    assert row.source_status_changed_count == 0
    assert row.screening_status_changed_count == 0
    assert row.research_bucket_changed_count == 0
    assert row.latest_generated_at is None
    assert row.top_stable_market_slug is None
    assert row.reason_codes_json == ["no_latest_candidates"]
    assert row.rows_json == []
    assert codec.from_db_row(row) == _empty_report()


def test_project_rank_stability_db_row_is_frozen() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.readonly = False  # type: ignore[misc]


def test_project_rank_stability_db_row_rejects_wrong_report_types_and_subclasses() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    with pytest.raises(ValueError, match="PaperProjectScreeningRankStabilityReport"):
        codec.to_db_row(object())

    report = _report()
    subclass = ProjectRankStabilityReportSubclass(**report.__dict__)
    with pytest.raises(ValueError, match="PaperProjectScreeningRankStabilityReport"):
        codec.to_db_row(subclass)


def test_project_rank_stability_db_row_rejects_wrong_row_types_and_subclasses() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    row = codec.to_db_row(_report())

    class ProjectRankStabilityDbRowSubclass(
        codec.PaperProjectScreeningRankStabilityDbRow,
    ):
        pass

    with pytest.raises(ValueError, match="PaperProjectScreeningRankStabilityDbRow"):
        codec.from_db_row(object())
    with pytest.raises(ValueError, match="PaperProjectScreeningRankStabilityDbRow"):
        codec.from_db_row(ProjectRankStabilityDbRowSubclass(**_row_values(row)))


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_project_rank_stability_db_row_rejects_false_report_flags_before_write(
    flag_name: str,
) -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    report = _report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)


def test_project_rank_stability_db_row_rejects_false_nested_row_flags_before_write() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    report = _report()
    object.__setattr__(report.rows[1], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        codec.to_db_row(report)


def test_project_rank_stability_db_row_rejects_corrupted_stored_payload_flags() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    row = codec.to_db_row(_report())
    payload = {
        **row.payload_json,
        "rows": [
            row.payload_json["rows"][0],
            {**row.payload_json["rows"][1], "paper_only": False},
        ],
    }
    malformed = codec.PaperProjectScreeningRankStabilityDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
            "rows_json": payload["rows"],
        },
    )

    with pytest.raises(ValueError, match="paper_only"):
        codec.from_db_row(malformed)


def test_project_rank_stability_db_row_rejects_recursive_floats_in_json_payloads() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match="rows_json"):
        replace(
            row,
            rows_json=[
                {**row.rows_json[0], "latest_screening_score": 0.72},
                row.rows_json[1],
            ],
        )
    with pytest.raises(ValueError, match="payload_json"):
        replace(row, payload_json={**row.payload_json, "bad_float": 0.1})


def test_project_rank_stability_db_row_rejects_malformed_stored_payload() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    row = codec.to_db_row(_report())
    payload = {key: value for key, value in row.payload_json.items() if key != "rows"}
    malformed = codec.PaperProjectScreeningRankStabilityDbRow(
        **{
            **_row_values(row),
            "report_sha256": _canonical_payload_sha256(payload),
            "payload_json": payload,
        },
    )

    with pytest.raises(ValueError, match="payload_json"):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "b" * 64}, "report_sha256"),
        ({"generated_at": datetime(2026, 6, 22, 13, 1, tzinfo=UTC)}, "generated_at"),
        ({"config_version": "project-screening-rank-stability-v1"}, "config_version"),
        ({"stability_status": "stable"}, "stability_status"),
        ({"reason_codes_json": ["stable_ready_candidates_present"]}, "reason_codes_json"),
        ({"source_report_count": 3}, "source_report_count"),
        ({"candidate_count": 3}, "candidate_count"),
        ({"stable_count": 2}, "stable_count"),
        ({"watch_count": 0}, "watch_count"),
        ({"blocked_count": 1}, "blocked_count"),
        ({"stable_ready_count": 0}, "stable_ready_count"),
        ({"unstable_ready_count": 0}, "unstable_ready_count"),
        ({"scoring_side_changed_count": 0}, "scoring_side_changed_count"),
        ({"source_status_changed_count": 1}, "source_status_changed_count"),
        ({"screening_status_changed_count": 1}, "screening_status_changed_count"),
        ({"research_bucket_changed_count": 1}, "research_bucket_changed_count"),
        ({"latest_generated_at": datetime(2026, 6, 22, 12, 54, tzinfo=UTC)}, "latest_generated_at"),
        ({"top_stable_market_slug": "gamma"}, "top_stable_market_slug"),
    ),
)
def test_project_rank_stability_db_row_rejects_materialized_payload_mismatches(
    overrides: dict[str, object],
    message: str,
) -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    row = codec.to_db_row(_report())
    malformed = codec.PaperProjectScreeningRankStabilityDbRow(
        **{**_row_values(row), **overrides},
    )

    with pytest.raises(ValueError, match=message):
        codec.from_db_row(malformed)


@pytest.mark.parametrize(
    ("overrides", "message"),
    (
        ({"report_sha256": "bad"}, "report_sha256"),
        ({"stability_status": "pass"}, "stability_status"),
        ({"source_report_count": True}, "source_report_count"),
        ({"reason_codes_json": "no_latest_candidates"}, "reason_codes_json"),
        ({"rows_json": {"market_slug": "alpha"}}, "rows_json"),
        ({"paper_only": False}, "paper_only"),
    ),
)
def test_project_rank_stability_db_row_validates_row_shape(
    overrides: dict[str, object],
    message: str,
) -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row as codec

    row = codec.to_db_row(_report())

    with pytest.raises(ValueError, match=message):
        codec.PaperProjectScreeningRankStabilityDbRow(
            **{**_row_values(row), **overrides},
        )


def test_project_rank_stability_db_row_module_is_pure_codec() -> None:
    from polymarket_alpha_lab import paper_project_screening_rank_stability_db_row

    assert paper_project_screening_rank_stability_db_row.__name__.endswith("_db_row")
    source = Path(
        "src/polymarket_alpha_lab/paper_project_screening_rank_stability_db_row.py",
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
