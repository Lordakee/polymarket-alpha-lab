from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_market_source_conflict_decay_report import (
    ResearchStrategyMarketSourceConflictDecayConfig,
    ResearchStrategyMarketSourceConflictDecayObservation,
    ResearchStrategyMarketSourceConflictDecayReasonCodeCount,
    ResearchStrategyMarketSourceConflictDecayReport,
    ResearchStrategyMarketSourceConflictDecayRow,
    build_research_strategy_market_source_conflict_decay_report,
    research_strategy_market_source_conflict_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    index: int,
    *,
    candidate_id: str = "candidate-alpha-raw-id",
    market_id: str = "market-alpha-raw-id",
    market_slug: str = "candidate-alpha-election-market",
    market_question: str = "Will Candidate Alpha win the election?",
    source_id: str | None = None,
    source_family: str = "official",
    source_probability: Decimal = d("0.800000"),
    reference_probability: Decimal = d("0.400000"),
    confidence_score: Decimal = d("1.000000"),
    observed_at: datetime | None = None,
    source_url: str | None = "https://example.invalid/private-source",
    source_text: str | None = "private source text must not leave input rows",
    reason_codes: tuple[str, ...] = (),
) -> ResearchStrategyMarketSourceConflictDecayObservation:
    return ResearchStrategyMarketSourceConflictDecayObservation(
        candidate_id=candidate_id,
        market_id=market_id,
        market_slug=market_slug,
        market_question=market_question,
        source_id=source_id or f"source-{index:03d}-raw-id",
        source_family=source_family,
        source_probability=source_probability,
        reference_probability=reference_probability,
        confidence_score=confidence_score,
        observed_at=(
            observed_at if observed_at is not None else GENERATED_AT - timedelta(minutes=30)
        ),
        source_url=source_url,
        source_text=source_text,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchStrategyMarketSourceConflictDecayConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyMarketSourceConflictDecayReport:
    return build_research_strategy_market_source_conflict_decay_report(
        rows,
        config=cfg or ResearchStrategyMarketSourceConflictDecayConfig(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_block_report_with_digest() -> None:
    conflict_report = report(())
    payload = research_strategy_market_source_conflict_decay_report_payload(
        conflict_report,
    )

    assert type(conflict_report) is ResearchStrategyMarketSourceConflictDecayReport
    assert conflict_report.generated_at == GENERATED_AT
    assert conflict_report.group_count == d("0.000000")
    assert conflict_report.observation_count == d("0.000000")
    assert conflict_report.pass_count == d("0.000000")
    assert conflict_report.watch_count == d("0.000000")
    assert conflict_report.block_count == d("0.000000")
    assert conflict_report.average_decayed_conflict_score == d("0.000000")
    assert conflict_report.max_conflict_delta == d("0.000000")
    assert conflict_report.status == "block"
    assert conflict_report.reason_codes == ("no_source_observations",)
    assert conflict_report.reason_code_counts == (
        ResearchStrategyMarketSourceConflictDecayReasonCodeCount(
            reason_code="no_source_observations",
            count=d("1.000000"),
        ),
    )
    assert conflict_report.rows == ()
    assert conflict_report.paper_only is True
    assert conflict_report.report_only is True
    assert conflict_report.readonly is True
    assert payload["derived_validation_digest"] == conflict_report.derived_validation_digest
    assert len(conflict_report.derived_validation_digest) == 64


def test_conflicts_are_grouped_redacted_decayed_and_deterministic_payload() -> None:
    rows = (
        observation(
            3,
            candidate_id="candidate-beta-raw-id",
            market_id="market-beta-raw-id",
            market_slug="candidate-beta-election-market",
            market_question="Will Candidate Beta win the election?",
            source_id="source-beta-analysis-raw-id",
            source_family="analysis",
            source_probability=d("0.460000"),
            reference_probability=d("0.400000"),
            source_url="https://example.invalid/private-beta-analysis",
            source_text="private beta analysis text",
        ),
        observation(
            2,
            source_id="source-alpha-analysis-raw-id",
            source_family="analysis",
            source_probability=d("0.550000"),
            reference_probability=d("0.400000"),
            confidence_score=d("0.800000"),
            observed_at=GENERATED_AT - timedelta(hours=2),
            source_url="https://example.invalid/private-alpha-analysis",
            source_text="private alpha analysis text",
            reason_codes=("manual_reviewed",),
        ),
        observation(
            4,
            candidate_id="candidate-beta-raw-id",
            market_id="market-beta-raw-id",
            market_slug="candidate-beta-election-market",
            market_question="Will Candidate Beta win the election?",
            source_id="source-beta-official-raw-id",
            source_family="official",
            source_probability=d("0.400000"),
            reference_probability=d("0.400000"),
            source_url="https://example.invalid/private-beta-official",
            source_text="private beta official text",
        ),
        observation(
            1,
            source_id="source-alpha-official-raw-id",
            source_family="official",
            source_probability=d("0.800000"),
            reference_probability=d("0.400000"),
        ),
    )

    conflict_report = report(rows)
    repeated_report = report(tuple(reversed(rows)))
    payload = research_strategy_market_source_conflict_decay_report_payload(
        conflict_report,
    )
    encoded = json.dumps(payload, sort_keys=True, separators=(",", ":"))

    assert conflict_report.status == "watch"
    assert conflict_report.group_count == d("2.000000")
    assert conflict_report.observation_count == d("4.000000")
    assert conflict_report.pass_count == d("1.000000")
    assert conflict_report.watch_count == d("1.000000")
    assert conflict_report.block_count == d("0.000000")
    assert conflict_report.average_decayed_conflict_score == d("0.143696")
    assert conflict_report.max_conflict_delta == d("0.400000")
    assert conflict_report.reason_codes == (
        "input_manual_reviewed",
        "market_source_conflict_pass",
        "source_conflict_watch",
    )
    assert conflict_report.reason_code_counts == (
        ResearchStrategyMarketSourceConflictDecayReasonCodeCount(
            reason_code="input_manual_reviewed",
            count=d("1.000000"),
        ),
        ResearchStrategyMarketSourceConflictDecayReasonCodeCount(
            reason_code="market_source_conflict_pass",
            count=d("1.000000"),
        ),
        ResearchStrategyMarketSourceConflictDecayReasonCodeCount(
            reason_code="source_conflict_watch",
            count=d("1.000000"),
        ),
    )
    assert conflict_report.derived_validation_digest == repeated_report.derived_validation_digest

    watch_row, pass_row = conflict_report.rows
    assert type(watch_row) is ResearchStrategyMarketSourceConflictDecayRow
    assert watch_row.market_group_digest != pass_row.market_group_digest
    assert watch_row.source_count == d("2.000000")
    assert watch_row.source_family_count == d("2.000000")
    assert watch_row.conflict_observation_count == d("2.000000")
    assert watch_row.average_conflict_delta == d("0.275000")
    assert watch_row.max_conflict_delta == d("0.400000")
    assert watch_row.average_recency_score == d("0.978261")
    assert watch_row.decayed_conflict_score == d("0.257392")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == ("input_manual_reviewed", "source_conflict_watch")
    assert pass_row.decayed_conflict_score == d("0.030000")
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("market_source_conflict_pass",)

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["market_group_digest"] == watch_row.market_group_digest
    assert payload["rows"][0]["decayed_conflict_score"] == "0.257392"
    assert payload["derived_validation_digest"] == conflict_report.derived_validation_digest
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ":0.5" not in encoded
    for raw_value in (
        "candidate-alpha-raw-id",
        "candidate-beta-raw-id",
        "market-alpha-raw-id",
        "market-beta-raw-id",
        "candidate-alpha-election-market",
        "candidate-beta-election-market",
        "Will Candidate Alpha win the election?",
        "source-alpha-official-raw-id",
        "https://example.invalid/private-alpha-analysis",
        "private alpha analysis text",
    ):
        assert raw_value not in encoded
    with pytest.raises(TypeError):
        payload["status"] = "pass"
    with pytest.raises(TypeError):
        payload["rows"].append({})


def test_block_status_digest_validation_and_manual_consistency() -> None:
    conflict_report = report(
        (
            observation(
                1,
                source_probability=d("0.950000"),
                reference_probability=d("0.050000"),
            ),
            observation(
                2,
                source_family="analysis",
                source_probability=d("0.900000"),
                reference_probability=d("0.100000"),
            ),
        ),
    )

    assert conflict_report.status == "block"
    assert conflict_report.block_count == d("1.000000")
    assert conflict_report.rows[0].decayed_conflict_score == d("0.850000")
    assert conflict_report.rows[0].reason_codes == ("source_conflict_block",)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(conflict_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(conflict_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="block_count"):
        replace(conflict_report, block_count=d("0.000000"))


def test_reason_code_counts_count_row_occurrences_not_unique_report_codes() -> None:
    conflict_report = report(
        (
            observation(
                1,
                source_probability=d("0.400000"),
                reference_probability=d("0.400000"),
            ),
            observation(
                2,
                candidate_id="candidate-beta-raw-id",
                market_id="market-beta-raw-id",
                market_slug="candidate-beta-election-market",
                market_question="Will Candidate Beta win the election?",
                source_id="source-beta-official-raw-id",
                source_probability=d("0.410000"),
                reference_probability=d("0.400000"),
            ),
        ),
    )

    assert conflict_report.reason_codes == ("market_source_conflict_pass",)
    assert conflict_report.pass_count == d("2.000000")
    assert conflict_report.reason_code_counts == (
        ResearchStrategyMarketSourceConflictDecayReasonCodeCount(
            reason_code="market_source_conflict_pass",
            count=d("2.000000"),
        ),
    )


def test_repeated_source_observations_are_counted_without_raw_source_ids() -> None:
    conflict_report = report(
        (
            observation(
                1,
                source_id="source-alpha-official-raw-id",
                source_probability=d("0.800000"),
                reference_probability=d("0.400000"),
            ),
            observation(
                2,
                source_id="source-alpha-official-raw-id",
                source_probability=d("0.700000"),
                reference_probability=d("0.400000"),
                observed_at=GENERATED_AT - timedelta(hours=2),
            ),
        ),
    )

    row = conflict_report.rows[0]
    assert row.source_count == d("2.000000")
    assert row.source_family_count == d("1.000000")
    assert row.conflict_observation_count == d("2.000000")
    assert row.status == "watch"


def test_decimal_strictness_frozen_flags_and_future_time_validation() -> None:
    conflict_report = report((observation(1),))

    with pytest.raises(FrozenInstanceError):
        conflict_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        conflict_report.rows[0].decayed_conflict_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="source_probability"):
        observation(1, source_probability=Decimal("0.8"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="confidence_score"):
        observation(1, confidence_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((observation(1),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (observation(1),),
            generated_at=_DatetimeSubclass(2026, 7, 9, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(1, observed_at=datetime(2026, 7, 9, 11, 0))
    with pytest.raises(ValueError, match="observed_at"):
        report((observation(1, observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(observation(1), paper_only=False)
    with pytest.raises(ValueError, match="reason_code"):
        observation(1, reason_codes=("wallet_surface",))


def test_public_api_and_owned_module_have_no_io_execution_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_market_source_conflict_decay_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_source_terms = (
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
        "sqlite",
        "os.environ",
    )
    forbidden_public_name_terms = (
        "auth",
        "dsn",
        "live",
        "order",
        "recommendation",
        "sizing",
        "table",
        "token",
        "trade",
        "wallet",
    )

    assert all(term not in source for term in forbidden_source_terms)

    import polymarket_alpha_lab.research_strategy_market_source_conflict_decay_report as api

    assert all(
        term not in public_name.lower()
        for public_name in api.__all__
        for term in forbidden_public_name_terms
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
