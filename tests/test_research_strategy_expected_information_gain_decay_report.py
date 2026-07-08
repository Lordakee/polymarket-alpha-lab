from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_strategy_expected_information_gain_decay_report import (
    ResearchStrategyExpectedInformationGainDecayConfig,
    ResearchStrategyExpectedInformationGainDecayObservation,
    ResearchStrategyExpectedInformationGainDecayReport,
    ResearchStrategyExpectedInformationGainDecayReportDigest,
    build_research_strategy_expected_information_gain_decay_report,
    research_strategy_expected_information_gain_decay_report_digest,
    research_strategy_expected_information_gain_decay_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> ResearchStrategyExpectedInformationGainDecayConfig:
    values = {
        "config_version": "research-strategy-expected-information-gain-decay-report-v0",
        "fresh_source_age_hours": d("2.000000"),
        "stale_source_age_span_hours": d("22.000000"),
        "watch_decay_threshold": d("0.250000"),
        "block_decay_threshold": d("0.650000"),
    }
    values.update(overrides)
    return ResearchStrategyExpectedInformationGainDecayConfig(**values)


def observation(
    public_research_key: str,
    *,
    source_age_hours: Decimal = d("2.000000"),
    remaining_uncertainty_probability: Decimal = d("1.000000"),
    market_movement_probability: Decimal = d("0.000000"),
    cost_drag_probability: Decimal = d("0.000000"),
    liquidity_reliability_probability: Decimal = d("1.000000"),
    resolution_ambiguity_probability: Decimal = d("0.000000"),
    observed_at: datetime = GENERATED_AT,
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchStrategyExpectedInformationGainDecayObservation:
    return ResearchStrategyExpectedInformationGainDecayObservation(
        public_research_key=public_research_key,
        observed_at=observed_at,
        source_age_hours=source_age_hours,
        remaining_uncertainty_probability=remaining_uncertainty_probability,
        market_movement_probability=market_movement_probability,
        cost_drag_probability=cost_drag_probability,
        liquidity_reliability_probability=liquidity_reliability_probability,
        resolution_ambiguity_probability=resolution_ambiguity_probability,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[ResearchStrategyExpectedInformationGainDecayObservation, ...],
    *,
    cfg: ResearchStrategyExpectedInformationGainDecayConfig | None = None,
) -> ResearchStrategyExpectedInformationGainDecayReport:
    return build_research_strategy_expected_information_gain_decay_report(
        rows,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_watch_report_tracks_all_decay_drivers_with_public_payload() -> None:
    decay_report = report(
        (
            observation("research-pass"),
            observation(
                "research-watch",
                source_age_hours=d("13.000000"),
                remaining_uncertainty_probability=d("0.500000"),
                market_movement_probability=d("0.400000"),
                cost_drag_probability=d("0.200000"),
                liquidity_reliability_probability=d("0.600000"),
                resolution_ambiguity_probability=d("0.200000"),
                upstream_reason_codes=("freshness_gap",),
            ),
        ),
    )

    payload = research_strategy_expected_information_gain_decay_report_payload(
        decay_report,
    )
    encoded = json.dumps(payload, sort_keys=True)

    assert type(decay_report) is ResearchStrategyExpectedInformationGainDecayReport
    assert decay_report.status == "watch"
    assert decay_report.input_count == d("2")
    assert decay_report.row_count == d("2")
    assert decay_report.pass_count == d("1")
    assert decay_report.watch_count == d("1")
    assert decay_report.block_count == d("0")
    assert decay_report.max_expected_information_gain_decay_score == d("0.380000")
    assert decay_report.average_expected_information_gain_decay_score == d("0.190000")
    assert decay_report.min_retained_information_gain_score == d("0.620000")
    assert decay_report.reason_codes == (
        "expected_information_gain_decay_watch",
        "source_aging_decay",
        "reduced_uncertainty_decay",
        "market_movement_decay",
        "cost_drag_decay",
        "liquidity_reliability_decay",
        "resolution_ambiguity_decay",
    )
    assert tuple(row.public_research_key for row in decay_report.rows) == (
        "research-watch",
        "research-pass",
    )

    watch_row = decay_report.rows[0]
    assert watch_row.source_aging_decay_score == d("0.500000")
    assert watch_row.reduced_uncertainty_decay_score == d("0.500000")
    assert watch_row.market_movement_decay_score == d("0.400000")
    assert watch_row.cost_drag_decay_score == d("0.200000")
    assert watch_row.liquidity_reliability_decay_score == d("0.400000")
    assert watch_row.resolution_ambiguity_decay_score == d("0.200000")
    assert watch_row.expected_information_gain_decay_score == d("0.380000")
    assert watch_row.retained_information_gain_score == d("0.620000")
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "expected_information_gain_decay_watch",
        "input_freshness_gap",
        "source_aging_decay",
        "reduced_uncertainty_decay",
        "market_movement_decay",
        "cost_drag_decay",
        "liquidity_reliability_decay",
        "resolution_ambiguity_decay",
    )

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["expected_information_gain_decay_score"] == "0.380000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_public_numeric_scalars(payload)
    assert ": 0.5" not in encoded


def test_block_report_from_full_decay_drivers() -> None:
    decay_report = report(
        (
            observation(
                "research-block",
                source_age_hours=d("24.000000"),
                remaining_uncertainty_probability=d("0.000000"),
                market_movement_probability=d("1.000000"),
                cost_drag_probability=d("1.000000"),
                liquidity_reliability_probability=d("0.000000"),
                resolution_ambiguity_probability=d("1.000000"),
            ),
        ),
    )

    row = decay_report.rows[0]

    assert decay_report.status == "block"
    assert decay_report.block_count == d("1")
    assert decay_report.next_step == "pause_report_only_eig_decay_review"
    assert row.status == "block"
    assert row.expected_information_gain_decay_score == d("1.000000")
    assert row.retained_information_gain_score == d("0.000000")
    assert row.reason_codes == (
        "expected_information_gain_decay_block",
        "source_aging_decay",
        "reduced_uncertainty_decay",
        "market_movement_decay",
        "cost_drag_decay",
        "liquidity_reliability_decay",
        "resolution_ambiguity_decay",
    )


def test_empty_input_returns_blocked_report_only_zero_digest() -> None:
    empty = report(())

    assert empty.status == "block"
    assert empty.input_count == d("0")
    assert empty.row_count == d("0")
    assert empty.pass_count == d("0")
    assert empty.watch_count == d("0")
    assert empty.block_count == d("0")
    assert empty.max_expected_information_gain_decay_score == d("0.000000")
    assert empty.average_expected_information_gain_decay_score == d("0.000000")
    assert empty.min_retained_information_gain_score == d("0.000000")
    assert empty.reason_codes == ("expected_information_gain_decay_no_inputs",)
    assert len(empty.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in empty.derived_validation_digest)
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True


def test_payload_digest_and_digest_report_are_deterministic_and_consistent() -> None:
    left = report(
        (
            observation("research-c", market_movement_probability=d("0.300000")),
            observation("research-a", market_movement_probability=d("0.100000")),
            observation("research-b", market_movement_probability=d("0.200000")),
        ),
    )
    right = report(
        (
            observation("research-b", market_movement_probability=d("0.200000")),
            observation("research-c", market_movement_probability=d("0.300000")),
            observation("research-a", market_movement_probability=d("0.100000")),
        ),
    )

    left_payload = research_strategy_expected_information_gain_decay_report_payload(left)
    right_payload = research_strategy_expected_information_gain_decay_report_payload(right)
    left_digest = research_strategy_expected_information_gain_decay_report_digest(left)
    right_digest = research_strategy_expected_information_gain_decay_report_digest(right)

    assert left_payload == right_payload
    assert type(left_digest) is ResearchStrategyExpectedInformationGainDecayReportDigest
    assert left_digest == right_digest
    assert left_digest.report_digest == left.derived_validation_digest
    assert left_digest.status == left.status
    assert left_digest.reason_codes == left.reason_codes
    assert left_digest.payload == research_strategy_expected_information_gain_decay_report_payload(
        left_digest,
    )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(left, derived_validation_digest="0" * 64)


def test_decimal_type_datetime_type_and_hard_flags_are_strict() -> None:
    with pytest.raises(ValueError, match="source_age_hours"):
        observation("research-safe", source_age_hours=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_drag_probability"):
        observation(
            "research-safe",
            cost_drag_probability=_DecimalSubclass("0.100000"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        replace(observation("research-safe"), observed_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_research_strategy_expected_information_gain_decay_report(
            (observation("research-safe"),),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="watch_decay_threshold"):
        config(watch_decay_threshold=d("0.700000"))

    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        observation("research-safe", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((observation("research-safe"),)), readonly=False)


def test_public_leak_rejection_blocks_sensitive_keys_values_and_language() -> None:
    forbidden_values = (
        ("public_research_key", "candidate-123"),
        ("public_research_key", "market_id_abc"),
        ("public_research_key", "market-slug-abc"),
        ("upstream_reason_codes", ("source_url",)),
        ("upstream_reason_codes", ("raw_question_text",)),
        ("upstream_reason_codes", ("wallet_surface",)),
        ("upstream_reason_codes", ("order_surface",)),
        ("upstream_reason_codes", ("trade_surface",)),
        ("upstream_reason_codes", ("live_surface",)),
    )

    for field_name, unsafe_value in forbidden_values:
        with pytest.raises(ValueError, match="unsafe"):
            replace(observation("research-safe"), **{field_name: unsafe_value})

    payload = research_strategy_expected_information_gain_decay_report_payload(
        report((observation("research-safe"),)),
    )
    unsafe_key_payload = dict(payload)
    unsafe_key_payload["market_slug"] = "raw"
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_expected_information_gain_decay_report_payload(unsafe_key_payload)

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["rows"] = [
        dict(payload["rows"][0], public_research_key="https://example.invalid/raw")
    ]
    with pytest.raises(ValueError, match="unsafe"):
        research_strategy_expected_information_gain_decay_report_payload(
            unsafe_value_payload,
        )


def test_public_dataclasses_are_frozen() -> None:
    decay_report = report((observation("research-safe"),))

    with pytest.raises(FrozenInstanceError):
        decay_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        decay_report.rows[0].expected_information_gain_decay_score = d("0")  # type: ignore[misc]


def test_module_scope_is_report_only_without_execution_or_sensitive_surfaces() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_strategy_expected_information_gain_decay_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "candidate_id",
        "market_id",
        "market_slug",
        "market-slug",
        "question",
        "source_url",
        "source_text",
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
    )

    assert all(term not in source for term in forbidden_terms)


def assert_no_public_numeric_scalars(value: object) -> None:
    for item in _walk_payload_values(value):
        assert type(item) not in (int, float)


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
