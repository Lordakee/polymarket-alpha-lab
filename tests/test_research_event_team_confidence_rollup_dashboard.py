from __future__ import annotations

import json
from dataclasses import asdict, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_event_team_confidence_rollup_dashboard import (
    DEFAULT_RESEARCH_EVENT_TEAM_CONFIDENCE_ROLLUP_DASHBOARD_CONFIG_VERSION,
    ResearchEventTeamConfidenceObservation,
    ResearchEventTeamConfidenceRollupConfig,
    ResearchEventTeamConfidenceRollupReport,
    build_research_event_team_confidence_rollup_dashboard,
    research_event_team_confidence_rollup_dashboard_digest,
    research_event_team_confidence_rollup_dashboard_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> ResearchEventTeamConfidenceRollupConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_TEAM_CONFIDENCE_ROLLUP_DASHBOARD_CONFIG_VERSION
        ),
        "min_team_count": d("2.000000"),
        "max_pass_confidence_spread": d("0.200000"),
        "min_pass_evidence_coverage_ratio": d("0.800000"),
        "min_pass_review_complete_ratio": d("1.000000"),
    }
    values.update(overrides)
    return ResearchEventTeamConfidenceRollupConfig(**values)


def _observation(
    team_key: str,
    confidence_score: Decimal,
    evidence_covered_count: Decimal,
    evidence_required_count: Decimal,
    *,
    coordination_key: str = "event-alpha-redacted",
    discipline: str = "macro",
    review_status: str = "complete",
    hard_flags: tuple[str, ...] = (),
) -> ResearchEventTeamConfidenceObservation:
    return ResearchEventTeamConfidenceObservation(
        coordination_key=coordination_key,
        team_key=team_key,
        discipline=discipline,
        confidence_score=confidence_score,
        evidence_covered_count=evidence_covered_count,
        evidence_required_count=evidence_required_count,
        review_status=review_status,
        hard_flags=hard_flags,
    )


def _walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in _walk(nested))
    return (value,)


def test_rollup_returns_pass_when_teams_align_and_reviews_are_complete() -> None:
    report = build_research_event_team_confidence_rollup_dashboard(
        (
            _observation("policy-team", d("0.720000"), d("4"), d("4"), discipline="policy"),
            _observation("macro-team", d("0.700000"), d("4"), d("4")),
            _observation("legal-team", d("0.750000"), d("3"), d("4"), discipline="legal"),
        ),
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(report, ResearchEventTeamConfidenceRollupReport)
    assert report.generated_at == GENERATED_AT
    assert report.public_status == "pass"
    assert report.coordination_status == "aligned_for_human_review"
    assert report.team_count == d("3.000000")
    assert report.pass_team_count == d("3.000000")
    assert report.watch_team_count == d("0.000000")
    assert report.block_team_count == d("0.000000")
    assert report.average_confidence_score == d("0.723333")
    assert report.confidence_spread == d("0.050000")
    assert report.evidence_coverage_ratio == d("0.916667")
    assert report.review_complete_ratio == d("1.000000")
    assert report.reason_codes == (
        "research_event_team_confidence_rollup_pass",
    )
    assert tuple(row.team_key for row in report.rows) == (
        "legal-team",
        "macro-team",
        "policy-team",
    )
    assert all(row.public_status == "pass" for row in report.rows)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_rollup_returns_watch_for_confidence_disagreement_evidence_gap_or_pending_review() -> None:
    report = build_research_event_team_confidence_rollup_dashboard(
        (
            _observation("macro-team", d("0.300000"), d("1"), d("4")),
            _observation(
                "legal-team",
                d("0.850000"),
                d("4"),
                d("4"),
                discipline="legal",
                review_status="pending",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.public_status == "watch"
    assert report.coordination_status == "coordinate_human_review"
    assert report.team_count == d("2.000000")
    assert report.pass_team_count == d("0.000000")
    assert report.watch_team_count == d("2.000000")
    assert report.block_team_count == d("0.000000")
    assert report.confidence_spread == d("0.550000")
    assert report.evidence_coverage_ratio == d("0.625000")
    assert report.review_complete_ratio == d("0.500000")
    assert report.reason_codes == (
        "research_event_team_confidence_rollup_confidence_divergence",
        "research_event_team_confidence_rollup_evidence_gap",
        "research_event_team_confidence_rollup_review_pending",
    )


def test_rollup_returns_block_for_hard_flags_or_blocked_review() -> None:
    report = build_research_event_team_confidence_rollup_dashboard(
        (
            _observation("macro-team", d("0.700000"), d("4"), d("4")),
            _observation(
                "legal-team",
                d("0.720000"),
                d("4"),
                d("4"),
                discipline="legal",
                hard_flags=("policy_block",),
            ),
            _observation(
                "audit-team",
                d("0.690000"),
                d("4"),
                d("4"),
                discipline="audit",
                review_status="blocked",
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.public_status == "block"
    assert report.coordination_status == "halt_for_human_recheck"
    assert report.team_count == d("3.000000")
    assert report.pass_team_count == d("1.000000")
    assert report.watch_team_count == d("0.000000")
    assert report.block_team_count == d("2.000000")
    assert report.hard_flag_count == d("1.000000")
    assert report.reason_codes == (
        "research_event_team_confidence_rollup_hard_flag",
        "research_event_team_confidence_rollup_review_blocked",
    )
    rows = {row.team_key: row for row in report.rows}
    assert rows["legal-team"].hard_flag_count == d("1.000000")
    assert rows["legal-team"].public_status == "block"
    assert rows["audit-team"].public_status == "block"


def test_rollup_rejects_non_decimal_public_numerics_and_invalid_public_types() -> None:
    with pytest.raises(ValueError, match="confidence_score"):
        _observation("float-team", 0.5, d("1"), d("1"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_covered_count"):
        _observation("int-team", d("0.500000"), 1, d("1"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_team_count"):
        _config(min_team_count=2)
    with pytest.raises(ValueError, match="max_pass_confidence_spread"):
        _config(max_pass_confidence_spread=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="confidence_score"):
        _observation("nan-team", Decimal("NaN"), d("1"), d("1"))
    with pytest.raises(ValueError, match="review_status"):
        _observation("review-team", d("0.500000"), d("1"), d("1"), review_status="ready")
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_team_confidence_rollup_dashboard(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )


def test_rollup_rejects_public_leaks_and_trading_language() -> None:
    with pytest.raises(ValueError, match="coordination_key"):
        _observation("macro-team", d("0.500000"), d("1"), d("1"), coordination_key="market_slug:abc")
    with pytest.raises(ValueError, match="team_key"):
        _observation("wallet-team", d("0.500000"), d("1"), d("1"))
    with pytest.raises(ValueError, match="team_key"):
        _observation("buy-signal-team", d("0.500000"), d("1"), d("1"))
    with pytest.raises(ValueError, match="hard_flags"):
        _observation(
            "macro-team",
            d("0.500000"),
            d("1"),
            d("1"),
            hard_flags=("source_url=https://private.example",),
        )

    report = build_research_event_team_confidence_rollup_dashboard(
        (_observation("macro-team", d("0.500000"), d("1"), d("1")),),
        config=_config(),
        generated_at=GENERATED_AT,
    )
    public = repr(asdict(report)).lower()
    for token in (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert token not in public

    payload = research_event_team_confidence_rollup_dashboard_payload(report)
    payload["wallet_address"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_team_confidence_rollup_dashboard_payload(payload)


def test_rollup_hard_flags_require_known_safe_values_and_true_paper_flags() -> None:
    with pytest.raises(ValueError, match="hard_flags"):
        _observation(
            "macro-team",
            d("0.500000"),
            d("1"),
            d("1"),
            hard_flags=("unknown_flag",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            _observation("macro-team", d("0.500000"), d("1"), d("1")),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)


def test_rollup_payload_is_deterministic_decimal_string_only_and_report_digest_consistent() -> None:
    rows = (
        _observation("policy-team", d("0.720000"), d("4"), d("4"), discipline="policy"),
        _observation("macro-team", d("0.700000"), d("4"), d("4")),
        _observation("legal-team", d("0.750000"), d("3"), d("4"), discipline="legal"),
    )
    first = build_research_event_team_confidence_rollup_dashboard(
        rows,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    second = build_research_event_team_confidence_rollup_dashboard(
        tuple(reversed(rows)),
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=3))),
    )

    first_payload = research_event_team_confidence_rollup_dashboard_payload(first)
    second_payload = research_event_team_confidence_rollup_dashboard_payload(second)
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":")) == json.dumps(
        second_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["team_count"] == "3.000000"
    assert first_payload["average_confidence_score"] == "0.723333"
    assert first_payload["confidence_spread"] == "0.050000"
    assert first_payload["public_status"] == "pass"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert [row["team_key"] for row in first_payload["rows"]] == [
        "legal-team",
        "macro-team",
        "policy-team",
    ]
    assert not any(isinstance(value, Decimal) for value in _walk(first_payload))
    assert not any(type(value) is int for value in _walk(first_payload))
    assert not any(type(value) is float for value in _walk(first_payload))

    digest = research_event_team_confidence_rollup_dashboard_digest(first)
    assert digest == research_event_team_confidence_rollup_dashboard_digest(first_payload)
    for key in (
        "generated_at",
        "coordination_key",
        "public_status",
        "coordination_status",
        "team_count",
        "average_confidence_score",
        "confidence_spread",
        "evidence_coverage_ratio",
        "review_complete_ratio",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ):
        assert digest[key] == first_payload[key]

    tampered = dict(first_payload)
    tampered["public_status"] = "trade"
    with pytest.raises(ValueError, match="public_status"):
        research_event_team_confidence_rollup_dashboard_payload(tampered)
