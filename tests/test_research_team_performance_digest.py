from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_performance_digest import (
    ResearchTeamPerformanceDigestConfig,
    ResearchTeamPerformanceObservation,
    ResearchTeamPerformanceRow,
    build_research_team_performance_digest,
    research_team_performance_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    domain: str = "macro_rates",
    calibration_error_ratio: Decimal = d("0.050000"),
    error_pattern_count: Decimal = d("0"),
    review_completion_ratio: Decimal = d("0.950000"),
    evidence_quality_score: Decimal = d("0.900000"),
    sample_count: Decimal = d("10"),
) -> ResearchTeamPerformanceObservation:
    return ResearchTeamPerformanceObservation(
        domain=domain,
        calibration_error_ratio=calibration_error_ratio,
        error_pattern_count=error_pattern_count,
        review_completion_ratio=review_completion_ratio,
        evidence_quality_score=evidence_quality_score,
        sample_count=sample_count,
    )


def digest(
    rows: tuple[ResearchTeamPerformanceObservation, ...],
    *,
    config: ResearchTeamPerformanceDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
):
    return build_research_team_performance_digest(
        rows,
        config=config or ResearchTeamPerformanceDigestConfig(),
        generated_at=generated_at,
    )


def test_stable_long_term_performance_passes_with_domain_aggregation() -> None:
    report = digest(
        (
            observation(domain="macro_rates", sample_count=d("8")),
            observation(
                domain="macro_rates",
                calibration_error_ratio=d("0.070000"),
                error_pattern_count=d("1"),
                review_completion_ratio=d("0.900000"),
                evidence_quality_score=d("0.880000"),
                sample_count=d("12"),
            ),
            observation(domain="crypto_assets", sample_count=d("10")),
        ),
    )

    assert report.status == "pass"
    assert report.domain_count == d("2")
    assert report.observation_count == d("3")
    assert report.sample_count == d("30")
    assert report.pass_domain_count == d("2")
    assert report.watch_domain_count == d("0")
    assert report.block_domain_count == d("0")
    assert tuple(row.domain for row in report.rows) == ("crypto_assets", "macro_rates")
    assert report.average_quality_risk_score == d("0.066733")
    assert report.reason_codes == ("research_team_performance_pass",)

    macro = report.rows[1]
    assert type(macro) is ResearchTeamPerformanceRow
    assert macro.observation_count == d("2")
    assert macro.sample_count == d("20")
    assert macro.calibration_error_ratio == d("0.062000")
    assert macro.error_pattern_count == d("1")
    assert macro.error_pattern_rate == d("0.050000")
    assert macro.review_completion_ratio == d("0.920000")
    assert macro.evidence_quality_score == d("0.888000")
    assert macro.quality_risk_score == d("0.075100")
    assert macro.status == "pass"
    assert macro.reason_codes == (
        "calibration_stable",
        "error_patterns_stable",
        "review_completion_sufficient",
        "evidence_quality_sufficient",
        "sample_size_sufficient",
    )


def test_watch_digest_flags_domains_that_need_review() -> None:
    report = digest(
        (
            observation(
                domain="sports",
                calibration_error_ratio=d("0.180000"),
                error_pattern_count=d("2"),
                review_completion_ratio=d("0.800000"),
                evidence_quality_score=d("0.720000"),
                sample_count=d("10"),
            ),
        ),
    )

    assert report.status == "watch"
    assert report.pass_domain_count == d("0")
    assert report.watch_domain_count == d("1")
    assert report.block_domain_count == d("0")
    assert report.reason_codes == ("research_team_performance_watch",)

    row = report.rows[0]
    assert row.status == "watch"
    assert row.error_pattern_rate == d("0.200000")
    assert row.quality_risk_score == d("0.214000")
    assert row.reason_codes == (
        "calibration_watch",
        "error_patterns_watch",
        "review_completion_watch",
        "evidence_quality_watch",
        "sample_size_sufficient",
    )


def test_block_digest_when_quality_is_insufficient() -> None:
    report = digest(
        (
            observation(
                domain="politics",
                calibration_error_ratio=d("0.320000"),
                error_pattern_count=d("3"),
                review_completion_ratio=d("0.500000"),
                evidence_quality_score=d("0.400000"),
                sample_count=d("5"),
            ),
        ),
    )

    row = report.rows[0]
    assert report.status == "block"
    assert report.block_domain_count == d("1")
    assert report.reason_codes == ("research_team_performance_block",)
    assert row.status == "block"
    assert row.error_pattern_rate == d("0.600000")
    assert row.quality_risk_score == d("0.496000")
    assert row.reason_codes == (
        "calibration_block",
        "error_patterns_block",
        "review_completion_block",
        "evidence_quality_block",
        "sample_size_sufficient",
    )


def test_strict_types_reject_non_decimal_subclasses_and_bad_statuses() -> None:
    with pytest.raises(ValueError, match="calibration_error_ratio"):
        observation(calibration_error_ratio=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality_score"):
        observation(evidence_quality_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="generated_at"):
        digest((observation(),), generated_at=datetime(2026, 7, 7, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        digest(
            (observation(),),
            generated_at=_DatetimeSubclass(2026, 7, 7, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="config"):
        build_research_team_performance_digest(
            (observation(),),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="status"):
        replace(digest((observation(),)).rows[0], status="blocked")


def test_public_payload_rejects_leaky_identifiers_and_execution_language() -> None:
    leaked_values = (
        "candidate_id=abc123",
        "market_slug=fed-rate-question",
        "https://example.com/source",
        "postgresql://user:pass@host/db",
        "wallet-auth-token",
        "buy recommendation",
    )

    for value in leaked_values:
        with pytest.raises(ValueError, match="unsafe public payload"):
            observation(domain=value)

    report = digest((observation(domain="macro_rates"),))
    payload = research_team_performance_digest_payload(report)
    encoded = json.dumps(payload, sort_keys=True)
    forbidden_public_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "postgresql://",
        "dsn",
        "wallet",
        "auth",
        "token",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    )
    assert all(fragment not in encoded.lower() for fragment in forbidden_public_fragments)


def test_hard_flags_and_frozen_dataclasses_are_enforced() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(ResearchTeamPerformanceDigestConfig(), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(observation(), readonly=False)

    report = digest((observation(),))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]


def test_payload_is_deterministic_and_decimal_only() -> None:
    inputs = (
        observation(domain="macro_rates", sample_count=d("8")),
        observation(domain="crypto_assets", sample_count=d("10")),
        observation(domain="macro_rates", sample_count=d("12")),
    )

    first = digest(inputs)
    second = digest(tuple(reversed(inputs)))
    first_payload = research_team_performance_digest_payload(first)
    second_payload = research_team_performance_digest_payload(second)

    assert first == second
    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-07T12:00:00+00:00"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert first_payload["sample_count"] == "30"
    assert first_payload["rows"][0]["quality_risk_score"] == "0.050000"


def test_owned_module_has_no_persistence_network_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_team_performance_digest.py"
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
