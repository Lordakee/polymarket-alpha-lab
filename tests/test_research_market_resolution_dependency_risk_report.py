from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_resolution_dependency_risk_report import (
    ResearchMarketResolutionDependencyInput,
    ResearchMarketResolutionDependencyRiskConfig,
    ResearchMarketResolutionDependencyRiskReport,
    ResearchMarketResolutionDependencyRiskRow,
    build_research_market_resolution_dependency_risk_report,
    research_market_resolution_dependency_risk_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def dependency(
    index: int,
    *,
    resolution_group_id: str = "resolution-bucket-alpha",
    raw_market_id: str | None = None,
    market_slug: str | None = None,
    market_question: str | None = None,
    dependency_id: str | None = None,
    dependency_kind: str = "official-result",
    is_unresolved: bool = False,
    official_source_observed_at: datetime | None = None,
    rule_clarity_score: Decimal = d("0.900000"),
    manual_escalation_urgency_score: Decimal = d("0.100000"),
    source_url: str | None = None,
    source_text: str | None = None,
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketResolutionDependencyInput:
    return ResearchMarketResolutionDependencyInput(
        resolution_group_id=resolution_group_id,
        raw_market_id=raw_market_id or f"0xRAW-MARKET-{index:03d}",
        market_slug=market_slug or f"raw-market-slug-{index:03d}",
        market_question=market_question or f"Will raw market question {index} resolve?",
        dependency_id=dependency_id or f"dependency-{index:03d}",
        dependency_kind=dependency_kind,
        is_unresolved=is_unresolved,
        official_source_observed_at=official_source_observed_at
        if official_source_observed_at is not None
        else GENERATED_AT - timedelta(minutes=30),
        rule_clarity_score=rule_clarity_score,
        manual_escalation_urgency_score=manual_escalation_urgency_score,
        source_url=source_url or f"https://official.example.test/source/{index}",
        source_text=source_text or f"Raw official source text {index}",
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[ResearchMarketResolutionDependencyInput, ...],
    *,
    config: ResearchMarketResolutionDependencyRiskConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketResolutionDependencyRiskReport:
    return build_research_market_resolution_dependency_risk_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def test_report_aggregates_dependency_risk_without_public_raw_market_or_source_values() -> None:
    risk_report = report(
        (
            dependency(
                1,
                resolution_group_id="resolution-bucket-watch",
                raw_market_id="secret-market-1",
                market_slug="will-team-alpha-win",
                market_question="Will Team Alpha win the final?",
                dependency_id="official-scoreboard",
                is_unresolved=True,
                official_source_observed_at=GENERATED_AT - timedelta(hours=12),
                rule_clarity_score=d("0.650000"),
                manual_escalation_urgency_score=d("0.550000"),
                source_url="https://official.example.test/scoreboard",
                source_text="Official scoreboard text should stay private.",
                reason_codes=("scoreboard_pending",),
            ),
            dependency(
                2,
                resolution_group_id="resolution-bucket-pass",
                raw_market_id="secret-market-2",
                market_slug="raw-pass-slug",
                market_question="Raw pass question?",
                dependency_id="exchange-notice",
                is_unresolved=False,
                official_source_observed_at=GENERATED_AT - timedelta(minutes=20),
                rule_clarity_score=d("0.950000"),
                manual_escalation_urgency_score=d("0.050000"),
                source_url="https://official.example.test/notice",
                source_text="Private notice text.",
            ),
            dependency(
                3,
                resolution_group_id="resolution-bucket-watch",
                dependency_id="governing-body",
                is_unresolved=False,
                official_source_observed_at=GENERATED_AT - timedelta(hours=2),
                rule_clarity_score=d("0.750000"),
                manual_escalation_urgency_score=d("0.200000"),
            ),
        ),
    )

    assert risk_report.status == "watch"
    assert risk_report.group_count == d("2.000000")
    assert risk_report.dependency_count == d("3.000000")
    assert risk_report.unresolved_external_dependency_count == d("1.000000")
    assert risk_report.pass_count == d("1.000000")
    assert risk_report.watch_count == d("1.000000")
    assert risk_report.blocked_count == d("0.000000")
    assert risk_report.average_official_source_freshness_score == d("0.958334")
    assert risk_report.average_rule_clarity_score == d("0.825000")
    assert risk_report.max_manual_escalation_urgency_score == d("0.550000")
    assert risk_report.reason_codes == (
        "all_external_dependencies_resolved",
        "input_scoreboard_pending",
        "manual_escalation_urgent",
        "official_source_fresh",
        "resolution_dependency_risk_pass",
        "resolution_dependency_risk_watch",
        "rule_clarity_clear",
        "rule_clarity_watch",
        "unresolved_external_dependencies",
    )

    pass_row, watch_row = risk_report.rows
    assert type(pass_row) is ResearchMarketResolutionDependencyRiskRow
    assert pass_row.resolution_group_id == "resolution-bucket-pass"
    assert pass_row.status == "pass"
    assert pass_row.dependency_count == d("1.000000")
    assert pass_row.unresolved_external_dependency_count == d("0.000000")
    assert pass_row.latest_official_source_age_seconds == d("1200.000000")
    assert pass_row.official_source_freshness_score == d("1.000000")
    assert pass_row.average_rule_clarity_score == d("0.950000")
    assert pass_row.max_manual_escalation_urgency_score == d("0.050000")
    assert pass_row.risk_score == d("0.025000")
    assert pass_row.reason_codes == (
        "all_external_dependencies_resolved",
        "official_source_fresh",
        "resolution_dependency_risk_pass",
        "rule_clarity_clear",
    )

    assert watch_row.resolution_group_id == "resolution-bucket-watch"
    assert watch_row.status == "watch"
    assert watch_row.dependency_count == d("2.000000")
    assert watch_row.unresolved_external_dependency_count == d("1.000000")
    assert watch_row.latest_official_source_age_seconds == d("7200.000000")
    assert watch_row.official_source_freshness_score == d("0.916667")
    assert watch_row.average_rule_clarity_score == d("0.700000")
    assert watch_row.max_manual_escalation_urgency_score == d("0.550000")
    assert watch_row.risk_score == d("0.358333")
    assert watch_row.reason_codes == (
        "input_scoreboard_pending",
        "manual_escalation_urgent",
        "official_source_fresh",
        "resolution_dependency_risk_watch",
        "rule_clarity_watch",
        "unresolved_external_dependencies",
    )

    payload = research_market_resolution_dependency_risk_report_payload(risk_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert "secret-market" not in encoded
    assert "will-team-alpha-win" not in encoded
    assert "Team Alpha" not in encoded
    assert "official.example.test" not in encoded
    assert "Official scoreboard text" not in encoded
    assert "raw_market_id" not in encoded
    assert "market_slug" not in encoded
    assert "market_question" not in encoded
    assert "source_url" not in encoded
    assert "source_text" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))


def test_empty_and_blocked_reports_are_deterministic_and_digest_validated() -> None:
    empty_report = report(())

    assert empty_report.status == "block"
    assert empty_report.rows == ()
    assert empty_report.group_count == d("0.000000")
    assert empty_report.reason_codes == ("no_resolution_dependencies",)

    blocked_report = report(
        (
            dependency(
                1,
                resolution_group_id="resolution-bucket-block",
                dependency_id="dep-a",
                is_unresolved=True,
                official_source_observed_at=GENERATED_AT - timedelta(days=3),
                rule_clarity_score=d("0.300000"),
                manual_escalation_urgency_score=d("0.900000"),
            ),
            dependency(
                2,
                resolution_group_id="resolution-bucket-block",
                dependency_id="dep-b",
                is_unresolved=True,
                official_source_observed_at=GENERATED_AT - timedelta(days=4),
                rule_clarity_score=d("0.350000"),
                manual_escalation_urgency_score=d("0.850000"),
            ),
            dependency(
                3,
                resolution_group_id="resolution-bucket-block",
                dependency_id="dep-c",
                is_unresolved=True,
                official_source_observed_at=GENERATED_AT - timedelta(days=5),
                rule_clarity_score=d("0.250000"),
                manual_escalation_urgency_score=d("0.950000"),
            ),
        ),
    )

    payload = research_market_resolution_dependency_risk_report_payload(blocked_report)
    unsigned_payload = dict(payload)
    expected_digest = unsigned_payload.pop("derived_validation_digest")
    canonical = json.dumps(
        unsigned_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )

    assert blocked_report.status == "block"
    assert blocked_report.blocked_count == d("1.000000")
    assert blocked_report.rows[0].status == "block"
    assert blocked_report.rows[0].unresolved_external_dependency_count == d("3.000000")
    assert blocked_report.rows[0].official_source_freshness_score == d("0.000000")
    assert blocked_report.rows[0].average_rule_clarity_score == d("0.300000")
    assert blocked_report.rows[0].max_manual_escalation_urgency_score == d("0.950000")
    assert blocked_report.rows[0].risk_score == d("0.912500")
    assert expected_digest == hashlib.sha256(canonical.encode("utf-8")).hexdigest()

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(blocked_report, derived_validation_digest="0" * 64)


def test_validation_rejects_bad_numerics_flags_statuses_and_future_sources() -> None:
    with pytest.raises(ValueError, match="fresh_official_source_age_seconds"):
        ResearchMarketResolutionDependencyRiskConfig(
            fresh_official_source_age_seconds=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="watch_rule_clarity_score"):
        ResearchMarketResolutionDependencyRiskConfig(
            watch_rule_clarity_score=DecimalSubclass("0.700000"),
        )
    with pytest.raises(ValueError, match="block_unresolved_dependency_count"):
        ResearchMarketResolutionDependencyRiskConfig(
            watch_unresolved_dependency_count=d("3.000000"),
            block_unresolved_dependency_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="is_unresolved"):
        replace(dependency(1), is_unresolved=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="rule_clarity_score"):
        dependency(1, rule_clarity_score=d("1.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        dependency(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(dependency(1), paper_only=False)
    with pytest.raises(ValueError, match="official_source_observed_at"):
        report(
            (
                dependency(
                    1,
                    official_source_observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_market_resolution_dependency_risk_report(
            (),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="status"):
        replace(report((dependency(1),)).rows[0], status="blocked")


def test_public_dataclasses_are_frozen_and_payload_requires_hard_flags() -> None:
    risk_report = report((dependency(1),))
    payload = research_market_resolution_dependency_risk_report_payload(risk_report)

    assert risk_report.paper_only is True
    assert risk_report.report_only is True
    assert risk_report.readonly is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    with pytest.raises(FrozenInstanceError):
        risk_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        risk_report.rows[0].risk_score = d("1.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="risk_score"):
        replace(risk_report.rows[0], risk_score=d("0.750000"))
    bad_payload = dict(payload)
    bad_payload["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        research_market_resolution_dependency_risk_report_payload(bad_payload)


def test_owned_module_has_no_db_network_wallet_order_sizing_or_recommendation_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_resolution_dependency_risk_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "wallet",
        "private_key",
        "auth",
        "order",
        "trade",
        "sizing",
        "recommendation",
        "recommend",
        "open(",
        "connect(",
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
