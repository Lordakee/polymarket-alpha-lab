from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_conflict_resolution_playbook import (
    ResearchConflictResolutionCase,
    ResearchConflictResolutionConfig,
    ResearchConflictResolutionPublicPayloadItem,
    ResearchConflictResolutionReport,
    ResearchConflictResolutionRow,
    build_research_conflict_resolution_playbook,
    research_conflict_resolution_playbook_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchConflictResolutionConfig:
    values = {
        "config_version": "research-conflict-resolution-playbook-v0",
        "pass_max_conflict_score": d("0.200000"),
        "block_min_conflict_score": d("0.700000"),
    }
    values.update(overrides)
    return ResearchConflictResolutionConfig(**values)


def case(
    index: int,
    *,
    claim_id: str = "claim-alpha",
    conflict_type: str = "factual_mismatch",
    review_status: str = "resolved",
    severity_score: Decimal | None = d("0.100000"),
    supplemental_information_needed: tuple[str, ...] = (),
    observed_at: datetime | None = None,
    public_summary: str = "Public evidence differs across reviewed sources.",
) -> ResearchConflictResolutionCase:
    return ResearchConflictResolutionCase(
        case_id=f"case-{index:03d}",
        claim_id=claim_id,
        conflict_type=conflict_type,
        evidence_ids=(f"evidence-{index:03d}", f"evidence-{index + 100:03d}"),
        source_families=("official", "analysis"),
        public_summary=public_summary,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=index),
        severity_score=severity_score,
        review_status=review_status,
        supplemental_information_needed=supplemental_information_needed,
    )


def build_report(
    rows: tuple[ResearchConflictResolutionCase, ...],
    *,
    cfg: ResearchConflictResolutionConfig | None = None,
    public_payload: tuple[ResearchConflictResolutionPublicPayloadItem, ...] = (),
    generated_at: datetime = GENERATED_AT,
) -> ResearchConflictResolutionReport:
    return build_research_conflict_resolution_playbook(
        rows,
        config=cfg or config(),
        public_payload=public_payload,
        generated_at=generated_at,
    )


def test_empty_input_returns_blocked_report_only_playbook() -> None:
    report = build_report(())

    assert type(report) is ResearchConflictResolutionReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-conflict-resolution-playbook-v0"
    assert report.case_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.blocked_count == d("0.000000")
    assert report.average_severity_score is None
    assert report.status == "blocked"
    assert report.rows == ()
    assert report.reason_codes == ("empty_conflict_resolution_queue",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_conflict_resolution_rows_cover_pass_watch_block_paths() -> None:
    report = build_report(
        (
            case(3, claim_id="z-claim", conflict_type="outcome_definition_mismatch", review_status="unreviewed", severity_score=d("0.850000"), supplemental_information_needed=("official_resolution_rule", "source_timestamp")),
            case(1, claim_id="a-claim", conflict_type="factual_mismatch", review_status="resolved", severity_score=d("0.100000")),
            case(2, claim_id="m-claim", conflict_type="timing_mismatch", review_status="in_review", severity_score=d("0.500000"), supplemental_information_needed=("timestamped_primary_source",)),
        ),
        public_payload=(
            ResearchConflictResolutionPublicPayloadItem(
                key="review_scope",
                value="Public conflict review only.",
            ),
        ),
    )

    assert report.status == "blocked"
    assert report.case_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.blocked_count == d("1.000000")
    assert report.average_severity_score == d("0.483333")
    assert tuple(row.claim_id for row in report.rows) == ("a-claim", "m-claim", "z-claim")

    pass_row, watch_row, block_row = report.rows
    assert type(pass_row) is ResearchConflictResolutionRow
    assert pass_row.status == "pass"
    assert pass_row.escalation_path == "none_required"
    assert pass_row.reason_codes == ("conflict_resolution_pass", "resolved_review_status")

    assert watch_row.status == "watch"
    assert watch_row.escalation_path == "source_owner_review"
    assert watch_row.supplemental_information_needed == ("timestamped_primary_source",)
    assert watch_row.reason_codes == (
        "in_review_review_status",
        "supplemental_information_needed",
        "timing_mismatch_conflict",
        "watch_conflict_score",
    )

    assert block_row.status == "blocked"
    assert block_row.escalation_path == "senior_research_review"
    assert block_row.reason_codes == (
        "block_conflict_score",
        "outcome_definition_mismatch_conflict",
        "supplemental_information_needed",
        "unreviewed_review_status",
    )


def test_payload_is_public_safe_and_has_no_float_or_int_numbers() -> None:
    report = build_report((case(1),))

    payload = research_conflict_resolution_playbook_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload == report.payload
    assert payload["rows"][0]["severity_score"] == "0.100000"
    assert payload["case_count"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(type(value) is int for value in _walk_payload_values(payload))
    assert ": 0.1" not in encoded

    unsafe_values = (
        "buy this outcome",
        "sell this outcome",
        "increase position",
        "wallet auth needed",
        "live order mutation",
        "connect to database",
        "write to network",
    )
    for unsafe in unsafe_values:
        with pytest.raises(ValueError, match="unsafe public value"):
            ResearchConflictResolutionPublicPayloadItem(key="scope", value=unsafe)


def test_validation_rejects_bad_types_unknown_enums_future_dates_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="pass_max_conflict_score"):
        config(pass_max_conflict_score=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="block_min_conflict_score"):
        config(block_min_conflict_score=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_report((case(1),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report((case(1),), generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="conflict_type"):
        case(1, conflict_type="price_view")
    with pytest.raises(ValueError, match="review_status"):
        case(1, review_status="approved")
    with pytest.raises(ValueError, match="severity_score"):
        case(1, severity_score=d("1.100000"))
    with pytest.raises(ValueError, match="severity_score"):
        case(1, severity_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        case(1, observed_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        build_report((case(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="supplemental_information_needed"):
        case(1, supplemental_information_needed=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(case(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    report = build_report((case(1),))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="case_count"):
        replace(report, case_count=d("2.000000"))


def test_owned_module_has_no_network_filesystem_execution_or_order_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_conflict_resolution_playbook.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlite",
        "psycopg",
        "sqlalchemy",
    )

    assert all(term not in source for term in forbidden_terms)


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
