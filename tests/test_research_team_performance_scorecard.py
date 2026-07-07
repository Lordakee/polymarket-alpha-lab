from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_team_performance_scorecard import (
    ResearchTeamPerformanceScorecardConfig,
    ResearchTeamPerformanceScorecardInput,
    ResearchTeamPerformanceScorecardReasonCodeCount,
    ResearchTeamPerformanceScorecardReport,
    ResearchTeamPerformanceScorecardRow,
    build_research_team_performance_scorecard_report,
    research_team_performance_scorecard_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchTeamPerformanceScorecardConfig:
    values = {
        "config_version": "research-team-performance-scorecard-v0",
        "maximum_pass_calibration_error": d("0.100000"),
        "maximum_watch_calibration_error": d("0.250000"),
        "minimum_pass_evidence_quality": d("0.750000"),
        "minimum_watch_evidence_quality": d("0.500000"),
        "minimum_pass_review_completion_rate": d("0.800000"),
        "minimum_watch_review_completion_rate": d("0.600000"),
        "minimum_pass_memory_update_quality": d("0.750000"),
        "minimum_watch_memory_update_quality": d("0.500000"),
        "minimum_evaluation_count": d("3.000000"),
    }
    values.update(overrides)
    return ResearchTeamPerformanceScorecardConfig(**values)


def team(
    team_id: str = "team-alpha",
    *,
    domain: str = "politics",
    calibration_error: Decimal = d("0.050000"),
    evidence_quality: Decimal = d("0.900000"),
    review_completion_rate: Decimal = d("0.850000"),
    memory_update_quality: Decimal = d("0.800000"),
    evaluation_count: Decimal = d("8.000000"),
    reason_codes: tuple[str, ...] = ("long_horizon_sample",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamPerformanceScorecardInput:
    return ResearchTeamPerformanceScorecardInput(
        team_id=team_id,
        domain=domain,
        calibration_error=calibration_error,
        evidence_quality=evidence_quality,
        review_completion_rate=review_completion_rate,
        memory_update_quality=memory_update_quality,
        evaluation_count=evaluation_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchTeamPerformanceScorecardInput,
    cfg: ResearchTeamPerformanceScorecardConfig | None = None,
) -> ResearchTeamPerformanceScorecardReport:
    return build_research_team_performance_scorecard_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_scorecard_rolls_up_pass_watch_and_block_team_performance() -> None:
    scorecard = report(
        team("politics-team", domain="politics"),
        team(
            "finance-team",
            domain="finance",
            calibration_error=d("0.180000"),
            evidence_quality=d("0.700000"),
            review_completion_rate=d("0.760000"),
            memory_update_quality=d("0.620000"),
            reason_codes=("needs_followup_cycle",),
        ),
        team(
            "sports-team",
            domain="sports",
            calibration_error=d("0.300000"),
            evidence_quality=d("0.490000"),
            review_completion_rate=d("0.550000"),
            memory_update_quality=d("0.400000"),
            evaluation_count=d("1.000000"),
            reason_codes=("thin_history",),
        ),
    )

    assert scorecard.status == "block"
    assert scorecard.team_count == d("3.000000")
    assert scorecard.pass_count == d("1.000000")
    assert scorecard.watch_count == d("1.000000")
    assert scorecard.block_count == d("1.000000")
    assert scorecard.average_composite_score == d("0.711667")
    assert scorecard.max_composite_score == d("0.875000")
    assert scorecard.min_composite_score == d("0.535000")
    assert tuple(row.team_id for row in scorecard.rows) == (
        "sports-team",
        "finance-team",
        "politics-team",
    )

    rows_by_id = {row.team_id: row for row in scorecard.rows}
    assert rows_by_id["politics-team"].status == "pass"
    assert rows_by_id["politics-team"].calibration_score == d("0.950000")
    assert rows_by_id["politics-team"].composite_score == d("0.875000")
    assert rows_by_id["politics-team"].reason_codes == (
        "long_horizon_sample",
        "team_performance_pass",
    )
    assert rows_by_id["finance-team"].status == "watch"
    assert rows_by_id["finance-team"].reason_codes == (
        "needs_followup_cycle",
        "calibration_error_watch",
        "evidence_quality_watch",
        "memory_update_quality_watch",
        "review_completion_rate_watch",
        "team_performance_watch",
    )
    assert rows_by_id["sports-team"].status == "block"
    assert rows_by_id["sports-team"].reason_codes == (
        "thin_history",
        "calibration_error_block",
        "evaluation_count_block",
        "evidence_quality_block",
        "memory_update_quality_block",
        "review_completion_rate_block",
        "team_performance_block",
    )
    assert scorecard.reason_code_counts[0] == ResearchTeamPerformanceScorecardReasonCodeCount(
        reason_code="calibration_error_block",
        count=d("1.000000"),
    )


def test_empty_scorecard_blocks_until_long_term_history_exists() -> None:
    scorecard = report()

    assert scorecard.status == "block"
    assert scorecard.reason_codes == ("team_performance_no_rows_block",)
    assert scorecard.team_count == ZERO
    assert scorecard.average_composite_score == ZERO
    assert scorecard.rows == ()
    assert scorecard.paper_only is True
    assert scorecard.report_only is True
    assert scorecard.readonly is True


def test_payload_is_deterministic_decimal_only_readonly_and_digest_checked() -> None:
    scorecard = report(team("deterministic-team", domain="finance"))

    assert is_dataclass(scorecard)
    assert len(scorecard.derived_validation_digest) == 64
    assert len(scorecard.rows[0].derived_validation_digest) == 64

    payload = research_team_performance_scorecard_payload(scorecard)
    encoded_once = json.dumps(payload, sort_keys=True)
    encoded_twice = json.dumps(
        research_team_performance_scorecard_payload(scorecard),
        sort_keys=True,
    )

    assert encoded_once == encoded_twice
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["team_count"] == "1.000000"
    assert payload["average_composite_score"] == "0.875000"
    assert payload["rows"][0]["calibration_error"] == "0.050000"
    assert payload["rows"][0]["calibration_score"] == "0.950000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(scorecard, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(scorecard.rows[0], composite_score=d("0.100000"))

    tampered_report = dict(payload)
    tampered_report["average_composite_score"] = "0.100000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_performance_scorecard_payload(tampered_report)

    tampered_row = dict(payload)
    tampered_row["rows"] = [dict(payload["rows"][0])]
    tampered_row["rows"][0]["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        research_team_performance_scorecard_payload(tampered_row)


def test_frozen_dataclasses_strict_types_flags_and_consistency_validation() -> None:
    scorecard = report(team("strict-team"))

    assert is_dataclass(ResearchTeamPerformanceScorecardConfig)
    assert is_dataclass(ResearchTeamPerformanceScorecardInput)
    assert is_dataclass(ResearchTeamPerformanceScorecardRow)
    assert is_dataclass(ResearchTeamPerformanceScorecardReasonCodeCount)
    assert is_dataclass(ResearchTeamPerformanceScorecardReport)
    with pytest.raises(FrozenInstanceError):
        scorecard.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        scorecard.rows[0].composite_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("SubTeamPerformanceRow", (ResearchTeamPerformanceScorecardRow,), {})

    with pytest.raises(ValueError, match="paper_only"):
        team(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(scorecard, readonly=False)
    with pytest.raises(ValueError, match="team_count"):
        replace(scorecard, team_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(scorecard, status="block")

    for item in (scorecard, *scorecard.rows, *scorecard.reason_code_counts):
        for field_name, value in item.__dict__.items():
            if field_name in {
                "paper_only",
                "report_only",
                "readonly",
                "derived_validation_digest",
            }:
                continue
            if isinstance(value, bool):
                continue
            assert type(value) is not int, field_name
            assert type(value) is not float, field_name

    with pytest.raises(ValueError, match="maximum_pass_calibration_error"):
        config(maximum_pass_calibration_error=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="maximum_watch_calibration_error"):
        config(maximum_watch_calibration_error=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_team_performance_scorecard_report(
            [],
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_team_performance_scorecard_report(
            [],
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="team_id"):
        team(team_id=" team")
    with pytest.raises(ValueError, match="domain"):
        team(domain="weather")
    with pytest.raises(ValueError, match="calibration_error"):
        team(calibration_error=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="evidence_quality"):
        team(evidence_quality=d("1.000001"))
    with pytest.raises(ValueError, match="evaluation_count"):
        team(evaluation_count=d("1.500000"))
    with pytest.raises(ValueError, match="reason_codes"):
        team(reason_codes=("duplicate", "duplicate"))


def test_public_payload_rejects_raw_identifiers_operational_terms_and_flag_downgrades() -> None:
    scorecard = report(team("public-safe"))
    payload = research_team_performance_scorecard_payload(scorecard)

    for unsafe_key in (
        "raw_candidate_ref",
        "raw_market_ref",
        "raw_source_ref",
        "raw_url_ref",
        "raw_text_ref",
        "raw_dsn_ref",
        "raw_table_ref",
        "raw_token_ref",
        "buy_hint",
        "sell_hint",
        "trade_hint",
        "position_hint",
        "recommendation_hint",
        "live_trading",
        "auth_ref",
        "wallet_ref",
        "order_ref",
        "mutation_ref",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[unsafe_key] = "blocked"
        with pytest.raises(ValueError, match="unsafe"):
            research_team_performance_scorecard_payload(unsafe_payload)

    for unsafe_value in (
        "candidate body",
        "market body",
        "source body",
        "url body",
        "text body",
        "dsn body",
        "table body",
        "token body",
        "buy now",
        "sell now",
        "trade now",
        "position now",
        "recommend now",
        "live trading",
        "auth secret",
        "wallet value",
        "order route",
        "mutation enabled",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload["summary"] = unsafe_value
        with pytest.raises(ValueError, match="unsafe"):
            research_team_performance_scorecard_payload(unsafe_payload)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        research_team_performance_scorecard_payload(downgraded)

    with pytest.raises(ValueError, match="unsafe"):
        team(team_id="market-alpha")
    with pytest.raises(ValueError, match="unsafe"):
        team(reason_codes=("auth_token_seen",))


def test_static_module_surface_has_no_external_io_or_float_literals() -> None:
    source = Path(
        "src/polymarket_alpha_lab/research_team_performance_scorecard.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for forbidden in (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "mysql",
        "redis",
        "kafka",
        "boto3",
    ):
        assert forbidden not in lowered
    parsed = ast.parse(source)
    assert not any(
        isinstance(node, ast.Constant) and isinstance(node.value, float)
        for node in ast.walk(parsed)
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    return tuple(values)
