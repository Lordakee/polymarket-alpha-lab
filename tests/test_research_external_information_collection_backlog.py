from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_external_information_collection_backlog import (
    ResearchExternalInformationCollectionBacklogConfig,
    ResearchExternalInformationCollectionBacklogNeed,
    ResearchExternalInformationCollectionBacklogReasonCodeCount,
    ResearchExternalInformationCollectionBacklogReport,
    ResearchExternalInformationCollectionBacklogRow,
    build_research_external_information_collection_backlog_report,
    research_external_information_collection_backlog_digest,
    research_external_information_collection_backlog_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchExternalInformationCollectionBacklogConfig:
    values = {
        "config_version": "research-external-information-collection-backlog-v0",
        "pass_backlog_score": d("0.700000"),
        "watch_automation_fit_score": d("0.400000"),
        "watch_public_safety_risk_score": d("0.300000"),
        "block_public_safety_risk_score": d("0.800000"),
    }
    values.update(overrides)
    return ResearchExternalInformationCollectionBacklogConfig(**values)


def need(
    index: int,
    *,
    private_request_key: str | None = None,
    collection_area: str = "resolution_rules",
    collection_tool: str = "agent_reach",
    information_need: str = "Confirm official resolution criteria are available",
    urgency_score: Decimal = d("0.800000"),
    automation_fit_score: Decimal = d("0.900000"),
    public_safety_risk_score: Decimal = d("0.050000"),
    requires_human_review: bool = False,
    hard_block_reasons: tuple[str, ...] = (),
    upstream_reason_codes: tuple[str, ...] = (),
) -> ResearchExternalInformationCollectionBacklogNeed:
    return ResearchExternalInformationCollectionBacklogNeed(
        private_request_key=private_request_key or f"private-request-{index:03d}",
        collection_area=collection_area,
        collection_tool=collection_tool,
        information_need=information_need,
        urgency_score=urgency_score,
        automation_fit_score=automation_fit_score,
        public_safety_risk_score=public_safety_risk_score,
        requires_human_review=requires_human_review,
        hard_block_reasons=hard_block_reasons,
        upstream_reason_codes=upstream_reason_codes,
    )


def report(
    needs: tuple[object, ...],
    *,
    cfg: ResearchExternalInformationCollectionBacklogConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchExternalInformationCollectionBacklogReport:
    return build_research_external_information_collection_backlog_report(
        needs,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_pass_watch_and_block_rows_are_summarized_as_public_report() -> None:
    backlog_report = report(
        (
            need(
                3,
                private_request_key="raw-candidate-blocked",
                collection_area="event_status",
                information_need="Determine if a public official status update exists",
                public_safety_risk_score=d("0.900000"),
                hard_block_reasons=("private_access_required",),
            ),
            need(
                1,
                private_request_key="raw-candidate-pass",
                information_need="Confirm official resolution criteria are available",
            ),
            need(
                2,
                private_request_key="raw-candidate-watch",
                collection_area="data_availability",
                collection_tool="scrapling",
                information_need="Check whether a public data release page needs review",
                automation_fit_score=d("0.350000"),
                public_safety_risk_score=d("0.250000"),
                requires_human_review=True,
            ),
        ),
    )

    assert type(backlog_report) is ResearchExternalInformationCollectionBacklogReport
    assert backlog_report.generated_at == GENERATED_AT
    assert backlog_report.request_count == d("3")
    assert backlog_report.pass_count == d("1")
    assert backlog_report.watch_count == d("1")
    assert backlog_report.block_count == d("1")
    assert backlog_report.status == "block"
    assert backlog_report.average_backlog_score == d("0.748333")
    assert backlog_report.reason_codes == (
        "automation_ready",
        "collection_backlog_block",
        "collection_backlog_pass",
        "collection_backlog_watch",
        "elevated_public_safety_risk",
        "human_review_required",
        "low_automation_fit",
        "private_access_required",
    )

    rows = backlog_report.rows
    assert tuple(row.public_request_ref for row in rows) == (
        "<collection-001>",
        "<collection-002>",
        "<collection-003>",
    )
    assert tuple(row.status for row in rows) == ("block", "pass", "watch")
    assert rows[0].next_step == "do_not_collect"
    assert rows[1].backlog_score == d("0.857500")
    assert rows[2].next_step == "route_to_manual_review"
    assert all(row.status in {"pass", "watch", "block"} for row in rows)
    assert all(row.paper_only and row.report_only and row.readonly for row in rows)


def test_type_and_decimal_validation_rejects_bad_values() -> None:
    with pytest.raises(ValueError, match="pass_backlog_score"):
        config(pass_backlog_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_public_safety_risk_score"):
        config(watch_public_safety_risk_score=_DecimalSubclass("0.300000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((need(1),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((need(1),), generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="urgency_score"):
        need(1, urgency_score="0.5")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="collection_area"):
        need(1, collection_area="candidate_market")
    with pytest.raises(ValueError, match="collection_tool"):
        need(1, collection_tool="browser")
    with pytest.raises(ValueError, match="requires_human_review"):
        replace(need(1), requires_human_review=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="status"):
        ResearchExternalInformationCollectionBacklogRow(
            public_request_ref="<collection-001>",
            collection_area="resolution_rules",
            collection_tool="agent_reach",
            information_need="Confirm official resolution criteria are available",
            urgency_score=d("0.800000"),
            automation_fit_score=d("0.900000"),
            public_safety_risk_score=d("0.050000"),
            backlog_score=d("0.857500"),
            status="pending",
            reason_codes=("automation_ready",),
            next_step="queue_public_collection",
        )


def test_public_payload_rejects_leaky_strings_and_omits_private_request_keys() -> None:
    with pytest.raises(ValueError, match="unsafe"):
        need(1, information_need="Check market_slug presidential-election")
    with pytest.raises(ValueError, match="unsafe"):
        need(1, information_need="Review source_url https://example.com/result")
    with pytest.raises(ValueError, match="unsafe"):
        need(1, information_need="Recommend buying yes after collecting data")

    backlog_report = report(
        (
            need(
                1,
                private_request_key="raw-candidate-123",
                information_need="Confirm official resolution criteria are available",
            ),
        ),
    )
    payload = research_external_information_collection_backlog_report_payload(
        backlog_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert "raw-candidate-123" not in encoded
    assert "private_request_key" not in encoded
    assert "market_id" not in encoded
    assert "market_slug" not in encoded
    assert "source_url" not in encoded
    assert "token" not in encoded
    assert "wallet" not in encoded
    assert "order" not in encoded


def test_hard_flags_are_required_everywhere() -> None:
    backlog_report = report((need(1),))

    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(need(1), readonly=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(backlog_report, report_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        ResearchExternalInformationCollectionBacklogReasonCodeCount(
            reason_code="automation_ready",
            count=d("1"),
            row_ratio=d("1.000000"),
            paper_only=False,
        )


def test_payload_is_deterministic_decimal_only_and_digest_matches_report() -> None:
    needs = (
        need(
            2,
            private_request_key="raw-candidate-watch",
            collection_area="data_availability",
            collection_tool="scrapling",
            information_need="Check whether a public data release page needs review",
            automation_fit_score=d("0.350000"),
            requires_human_review=True,
        ),
        need(
            1,
            private_request_key="raw-candidate-pass",
            information_need="Confirm official resolution criteria are available",
        ),
        need(
            3,
            private_request_key="raw-candidate-blocked",
            collection_area="event_status",
            information_need="Determine if a public official status update exists",
            hard_block_reasons=("execution_surface_required",),
        ),
    )
    first_report = report(needs)
    second_report = report(tuple(reversed(needs)))

    first_payload = research_external_information_collection_backlog_report_payload(
        first_report,
    )
    second_payload = research_external_information_collection_backlog_report_payload(
        second_report,
    )
    digest = research_external_information_collection_backlog_digest(first_report)

    assert first_payload == second_payload
    assert first_payload["digest"] == digest
    assert digest["status"] == first_report.status
    assert digest["request_count"] == str(first_report.request_count)
    assert digest["block_count"] == str(first_report.block_count)
    assert tuple(row["public_request_ref"] for row in digest["priority_items"]) == (
        "<collection-001>",
        "<collection-002>",
        "<collection-003>",
    )
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert ": 0.5" not in json.dumps(first_payload, sort_keys=True)


def test_public_dataclasses_are_frozen_and_manual_consistency_is_validated() -> None:
    backlog_report = report((need(1),))

    with pytest.raises(FrozenInstanceError):
        backlog_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        backlog_report.rows[0].backlog_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(backlog_report.rows[0], reason_codes=("human_review_required",))
    with pytest.raises(ValueError, match="pass_count"):
        replace(backlog_report, pass_count=d("0"))


def test_owned_module_has_no_collection_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_external_information_collection_backlog.py"
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
        "wallet_",
        "order_",
        "trade_",
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
