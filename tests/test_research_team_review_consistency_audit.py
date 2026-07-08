from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import importlib
import json
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def audit_module() -> object:
    try:
        return importlib.import_module(
            "polymarket_alpha_lab.research_team_review_consistency_audit",
        )
    except ModuleNotFoundError as exc:
        pytest.fail(f"research team review consistency audit module is missing: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def review(
    research_item_id: str,
    team_id: str,
    *,
    review_status: str = "pass",
    reason_codes: tuple[str, ...] = ("source_quality_pass",),
    evidence_gap_codes: tuple[str, ...] = (),
    escalation_required: bool = False,
    reviewed_at: datetime | None = None,
    public_notes: str = "reviewed public evidence",
) -> object:
    m = audit_module()
    return m.ResearchTeamReviewConsistencyInput(
        research_item_id=research_item_id,
        team_id=team_id,
        review_status=review_status,
        reviewed_at=reviewed_at or GENERATED_AT - timedelta(minutes=15),
        reason_codes=reason_codes,
        evidence_gap_codes=evidence_gap_codes,
        escalation_required=escalation_required,
        public_notes=public_notes,
    )


def build_report(reviews: tuple[object, ...]) -> object:
    m = audit_module()
    return m.build_research_team_review_consistency_audit(
        reviews,
        config=m.ResearchTeamReviewConsistencyConfig(),
        generated_at=GENERATED_AT,
    )


def test_audit_report_covers_pass_watch_block_divergence_and_escalation() -> None:
    m = audit_module()

    report = build_report(
        (
            review("alpha", "macro"),
            review("alpha", "liquidity"),
            review("beta", "macro", review_status="pass"),
            review("beta", "liquidity", review_status="watch"),
            review("gamma", "macro", reason_codes=("source_quality_pass",)),
            review(
                "gamma",
                "liquidity",
                reason_codes=("missing_resolution_source",),
                evidence_gap_codes=("missing_primary_source",),
            ),
            review("delta", "macro", review_status="pass"),
            review(
                "delta",
                "liquidity",
                review_status="pass",
                escalation_required=True,
                reason_codes=("manual_escalation_requested",),
            ),
        ),
    )

    assert type(report) is m.ResearchTeamReviewConsistencyAuditReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "research-team-review-consistency-audit-v0"
    assert report.audit_status == "block"
    assert report.next_step == "resolve_research_review_consistency_blocks"
    assert report.review_item_count == d("4")
    assert report.team_review_count == d("8")
    assert report.pass_count == d("1")
    assert report.watch_count == d("1")
    assert report.block_count == d("2")
    assert report.status_divergence_count == d("1")
    assert report.reason_code_divergence_count == d("2")
    assert report.evidence_gap_divergence_count == d("1")
    assert report.escalation_required_count == d("1")
    assert tuple(row.research_item_id for row in report.rows) == (
        "alpha",
        "beta",
        "delta",
        "gamma",
    )

    alpha, beta, delta, gamma = report.rows
    assert alpha.audit_status == "pass"
    assert alpha.reason_codes == (
        "research_team_review_consistency_pass",
        "review_consensus_clear",
    )
    assert beta.audit_status == "block"
    assert beta.status_values == ("pass", "watch")
    assert beta.reason_codes == (
        "research_team_review_consistency_block",
        "status_divergence",
    )
    assert delta.audit_status == "block"
    assert delta.escalation_required_count == d("1")
    assert "escalation_required" in delta.reason_codes
    assert gamma.audit_status == "watch"
    assert gamma.reason_code_divergence_count == d("1")
    assert gamma.evidence_gap_divergence_count == d("1")
    assert gamma.reason_codes == (
        "evidence_gap_divergence",
        "reason_code_divergence",
        "research_team_review_consistency_watch",
    )

    assert tuple(
        (count.reason_code, count.count)
        for count in report.reason_code_counts
        if count.reason_code.endswith("divergence")
    ) == (
        ("evidence_gap_divergence", d("1")),
        ("reason_code_divergence", d("1")),
        ("status_divergence", d("1")),
    )


def test_payload_is_public_safe_deterministic_and_decimal_only() -> None:
    m = audit_module()
    report = build_report(
        (
            review("zeta", "risk"),
            review("alpha", "macro"),
            review("alpha", "liquidity"),
            review("zeta", "macro"),
        ),
    )

    payload = m.research_team_review_consistency_audit_payload(report)
    encoded = json.dumps(payload, sort_keys=True)

    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["review_item_count"] == "2"
    assert payload["team_review_count"] == "4"
    assert [row["research_item_id"] for row in payload["rows"]] == ["alpha", "zeta"]
    assert payload["rows"][0]["team_count"] == "2"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert "0.5" not in encoded
    assert not _payload_has_unsafe_key(payload)


def test_validation_rejects_bad_types_unsafe_text_and_bad_flags() -> None:
    m = audit_module()

    with pytest.raises(ValueError, match="min_team_review_count"):
        m.ResearchTeamReviewConsistencyConfig(min_team_review_count=2)
    with pytest.raises(ValueError, match="min_team_review_count"):
        m.ResearchTeamReviewConsistencyConfig(
            min_team_review_count=_DecimalSubclass("2"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        m.build_research_team_review_consistency_audit(
            (review("alpha", "macro"),),
            config=m.ResearchTeamReviewConsistencyConfig(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        m.build_research_team_review_consistency_audit(
            (review("alpha", "macro"),),
            config=m.ResearchTeamReviewConsistencyConfig(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="review_status"):
        review("alpha", "macro", review_status="ready")
    with pytest.raises(ValueError, match="reason_codes"):
        review("alpha", "macro", reason_codes=["source_quality_pass"])  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="escalation_required"):
        review("alpha", "macro", escalation_required=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="public_notes"):
        review("alpha", "macro", public_notes="place order after review")
    with pytest.raises(ValueError, match="public_notes"):
        review("alpha", "macro", public_notes="token=secret")
    with pytest.raises(ValueError, match="paper_only"):
        replace(review("alpha", "macro"), paper_only=False)
    with pytest.raises(ValueError, match="reviewed_at"):
        build_report((review("alpha", "macro", reviewed_at=GENERATED_AT + timedelta(seconds=1)),))


def test_public_dataclasses_are_frozen_and_manual_consistency_is_validated() -> None:
    report = build_report((review("alpha", "macro"), review("alpha", "liquidity")))

    with pytest.raises(FrozenInstanceError):
        report.audit_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].audit_status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="audit_status"):
        replace(report.rows[0], audit_status="block")
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("10"))


def test_owned_module_has_no_network_filesystem_execution_or_unsafe_public_fields() -> None:
    m = audit_module()
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_review_consistency_audit.py"
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
        "psycopg",
        "sqlalchemy",
    )

    assert all(term not in source for term in forbidden_terms)
    for cls in (
        m.ResearchTeamReviewConsistencyConfig,
        m.ResearchTeamReviewConsistencyInput,
        m.ResearchTeamReviewConsistencyAuditRow,
        m.ResearchTeamReviewConsistencyReasonCodeCount,
        m.ResearchTeamReviewConsistencyAuditReport,
    ):
        for field in fields(cls):
            assert not any(
                fragment in field.name.lower()
                for fragment in ("wallet", "auth", "order")
            )


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


def _payload_has_unsafe_key(value: object) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if any(fragment in key.lower() for fragment in ("wallet", "auth", "order")):
                return True
            if _payload_has_unsafe_key(item):
                return True
    elif isinstance(value, list):
        return any(_payload_has_unsafe_key(item) for item in value)
    return False
