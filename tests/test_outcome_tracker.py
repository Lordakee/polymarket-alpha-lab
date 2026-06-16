"""Functional tests for ``polymarket_alpha_lab.outcome_tracker``.

Stage 9 RED+GREEN: a fake Protocol-only client returns raw Gamma payloads with
``outcomePrices``; ``check_outcomes`` must build one observation per resolved
trade LEG (never deduplicated by ``condition_id``), skip pending markets, match
outcome labels case-insensitively through YES_NAMES/NO_NAMES, and read the
winner from ``outcomePrices`` (never ``resolutionStatus``).

These tests deliberately construct ``PaperTradeRecord`` values via the journal
factory (``PaperTradeRecord.from_packet_and_fill``) and round-trip them through
``PaperTradeJournal`` so the reader path the real ``check_outcomes`` uses is
exercised end to end.
"""

from __future__ import annotations

from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.forecast_evidence import PaperForecastEvidenceReport
from polymarket_alpha_lab.journal import PaperTradeJournal, PaperTradeRecord
from polymarket_alpha_lab.outcome_tracker import (
    OutcomeTrackingConfig,
    OutcomeTrackingReport,
    check_outcomes,
)
from polymarket_alpha_lab.paper import PaperFill
from polymarket_alpha_lab.pipeline import ScoredCandidate
from polymarket_alpha_lab.research import build_research_packet


GENERATED_AT = datetime(2026, 6, 16, 12, 0, tzinfo=UTC)
DECISION_AT = datetime(2026, 6, 13, 12, 31, tzinfo=UTC)
PACKET_CREATED_AT = datetime(2026, 6, 13, 12, 30, tzinfo=UTC)
ORDER_BOOK_AT = datetime(2026, 6, 13, 12, 30, 30, tzinfo=UTC)


class FakeGammaClient:
    """Protocol-only fake returning a canned closed-market slice.

    Mirrors the ``OutcomeTrackerClient`` Protocol: only ``list_markets`` is
    needed. Returns raw Gamma-shaped payloads (dicts with ``outcomes`` /
    ``outcomePrices`` as native lists OR JSON strings) so the tracker's
    ``outcomePrices`` reader is exercised, never ``resolutionStatus``.
    """

    def __init__(self, payloads: list[dict]) -> None:
        self._payloads = payloads
        self.calls: list[dict] = []

    def list_markets(self, *, active: bool, closed: bool, limit: int):
        self.calls.append({"active": active, "closed": closed, "limit": limit})
        return list(self._payloads)


def _build_record(
    *,
    condition_id: str,
    token_id: str,
    market_slug: str,
    outcome_name: str,
    packet_id: str,
    fair_value_estimate: Decimal,
    model_probability: Decimal | None = None,
) -> PaperTradeRecord:
    packet = build_research_packet(
        candidate=ScoredCandidate(
            condition_id=condition_id,
            token_id=token_id,
            market_slug=market_slug,
            question=f"Will {market_slug} resolve yes?",
            total_score="80.000",
            raw_archive_path="data/raw/gamma/markets.json",
        ),
        created_at=PACKET_CREATED_AT,
        market_url=f"https://polymarket.com/event/{market_slug}",
        outcome_name=outcome_name,
        strategy_type="market_quality",
        model_probability=model_probability if model_probability is not None else fair_value_estimate,
        bid=Decimal("0.50"),
        ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        expected_entry_price=Decimal("0.52"),
        fair_value_estimate=fair_value_estimate,
        theoretical_edge=Decimal("0.03"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
        cost_adjusted_edge=Decimal("0.02"),
        confidence=Decimal("0.60"),
        max_executable_size=Decimal("100"),
        risk_tags=("liquidity",),
        thesis="Tight spread and clear rules.",
        invalidating_conditions="Spread widens.",
        rule_text="Example rule.",
        resolution_source="Example source",
    )
    fill = PaperFill(
        token_id=token_id,
        side="buy",
        requested_size=Decimal("10"),
        order_book_captured_at=ORDER_BOOK_AT,
        order_book_snapshot_sha256="a" * 64,
        filled_size=Decimal("10"),
        unfilled_size=Decimal("0"),
        average_price=Decimal("0.52"),
        worst_price=Decimal("0.52"),
        best_bid=Decimal("0.50"),
        best_ask=Decimal("0.52"),
        midpoint=Decimal("0.51"),
        spread=Decimal("0.02"),
        slippage_estimate=Decimal("0.004"),
    )
    return PaperTradeRecord.from_packet_and_fill(
        packet=packet,
        fill=fill,
        decision_timestamp=DECISION_AT,
        order_book_raw_archive_path="data/raw/clob/book.json",
        order_book_raw_payload_sha256="b" * 64,
        account_equity_before_trade=Decimal("10000"),
        sizing_limiter="max_executable_size",
        planned_exit_rule="Mark at executable bid on review.",
    )


def _write_journal(tmp_path: Path, records: list[PaperTradeRecord]) -> Path:
    journal_path = tmp_path / "paper-trades.jsonl"
    # Always materialize the file (even when empty) so PaperTradeJournal.read
    # sees a present, zero-record journal rather than FileNotFoundError.
    journal_path.touch()
    journal = PaperTradeJournal(journal_path)
    for record in records:
        journal.append(record)
    return journal_path


def _yes_won_payload(condition_id: str, *, closed: bool = True) -> dict:
    return {
        "conditionId": condition_id,
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["1", "0"],
        "closed": closed,
        "active": not closed,
        # resolutionStatus deliberately omitted/None to prove the tracker does
        # NOT rely on it (CRITICAL fix #1).
        "resolutionStatus": None,
    }


def _no_won_payload(condition_id: str, *, closed: bool = True) -> dict:
    return {
        "conditionId": condition_id,
        "outcomes": ["Yes", "No"],
        "outcomePrices": ["0", "1"],
        "closed": closed,
        "active": not closed,
        "resolutionStatus": "",
    }


def test_resolved_yes_leg_won_produces_observation_with_actual_one(tmp_path):
    record = _build_record(
        condition_id="0xYES1",
        token_id="111",
        market_slug="m-yes-1",
        outcome_name="YES",
        packet_id="pkt-yes-1",
        fair_value_estimate=Decimal("0.60"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient([_yes_won_payload("0xYES1")])

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, OutcomeTrackingReport)
    assert report.total_markets_checked == 1
    assert report.resolved_count == 1
    assert report.pending_count == 0
    assert len(report.observations) == 1
    assert report.paper_only is True
    assert report.report_only is True
    observation = report.observations[0]
    assert observation.condition_id == "0xYES1"
    assert observation.token_id == "111"
    assert observation.source_packet_id == record.packet_id
    assert observation.predicted_probability == Decimal("0.60")
    assert observation.actual_outcome_value == Decimal("1")
    assert observation.observed_at == GENERATED_AT
    assert isinstance(report.forecast_evidence_report, PaperForecastEvidenceReport)
    # The client must have requested the CLOSED Gamma slice.
    assert client.calls == [{"active": False, "closed": True, "limit": 500}]


def test_resolved_no_leg_when_yes_won_produces_observation_with_actual_zero(tmp_path):
    # CRITICAL #1 + IMPORTANT #2: trade was BUY NO, market resolved YES (winner
    # read from outcomePrices=["1","0"], label matched case-insensitively).
    record = _build_record(
        condition_id="0xNO1",
        token_id="222",
        market_slug="m-no-1",
        outcome_name="NO",
        packet_id="pkt-no-1",
        fair_value_estimate=Decimal("0.40"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient([_yes_won_payload("0xNO1")])

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.resolved_count == 1
    observation = report.observations[0]
    assert observation.actual_outcome_value == Decimal("0")
    assert observation.predicted_probability == Decimal("0.40")


def test_no_leg_wins_when_no_won_produces_observation_with_actual_one(tmp_path):
    record = _build_record(
        condition_id="0xNO2",
        token_id="333",
        market_slug="m-no-2",
        outcome_name="NO",
        packet_id="pkt-no-2",
        fair_value_estimate=Decimal("0.45"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient([_no_won_payload("0xNO2")])

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    observation = report.observations[0]
    assert observation.actual_outcome_value == Decimal("1")


def test_pending_open_market_produces_no_observation(tmp_path):
    # IMPORTANT #3 boundary: market still open (closed=False, active=True) with
    # mid-market outcomePrices -> PENDING, never an observation.
    record = _build_record(
        condition_id="0xOPEN",
        token_id="444",
        market_slug="m-open",
        outcome_name="YES",
        packet_id="pkt-open",
        fair_value_estimate=Decimal("0.55"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient(
        [
            {
                "conditionId": "0xOPEN",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.55", "0.45"],
                "closed": False,
                "active": True,
            }
        ]
    )

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.total_markets_checked == 1
    assert report.resolved_count == 0
    assert report.pending_count == 1
    assert report.observations == ()
    assert report.forecast_evidence_report is None


def test_pending_when_market_payload_missing_from_gamma(tmp_path):
    record = _build_record(
        condition_id="0xMISSING",
        token_id="555",
        market_slug="m-missing",
        outcome_name="YES",
        packet_id="pkt-missing",
        fair_value_estimate=Decimal("0.50"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient([])  # Gamma returned no closed markets

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.resolved_count == 0
    assert report.pending_count == 1
    assert report.observations == ()


def test_one_observation_per_resolved_leg_not_deduplicated_by_condition_id(tmp_path):
    # IMPORTANT #3: YES and NO legs on the SAME condition_id are independent
    # calibration points. Two resolved legs -> two observations, even though
    # they share a market.
    yes_leg = _build_record(
        condition_id="0xSHARED",
        token_id="666",
        market_slug="m-shared",
        outcome_name="YES",
        packet_id="pkt-shared-yes",
        fair_value_estimate=Decimal("0.62"),
    )
    no_leg = _build_record(
        condition_id="0xSHARED",
        token_id="777",
        market_slug="m-shared",
        outcome_name="NO",
        packet_id="pkt-shared-no",
        fair_value_estimate=Decimal("0.38"),
    )
    journal_path = _write_journal(tmp_path, [yes_leg, no_leg])
    client = FakeGammaClient([_yes_won_payload("0xSHARED")])

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.total_markets_checked == 2
    assert report.resolved_count == 2  # one per leg, NOT deduped
    assert report.pending_count == 0
    assert len(report.observations) == 2
    by_token = {obs.token_id: obs for obs in report.observations}
    assert by_token["666"].actual_outcome_value == Decimal("1")  # YES won
    assert by_token["777"].actual_outcome_value == Decimal("0")  # NO lost
    assert by_token["666"].source_packet_id == yes_leg.packet_id
    assert by_token["777"].source_packet_id == no_leg.packet_id
    assert by_token["666"].condition_id == "0xSHARED"
    assert by_token["777"].condition_id == "0xSHARED"


def test_case_insensitive_alias_matching_yes_true_long_and_no_false_short(tmp_path):
    # IMPORTANT #2: trade outcome_name uppercase ("YES"/"NO"); Gamma labels
    # title-case ("Yes"/"No"). The alias sets (yes/true/long, no/false/short)
    # must normalize both. Also exercise alternate aliases via Gamma labels.
    record_yes = _build_record(
        condition_id="0xCASE1",
        token_id="888",
        market_slug="m-case-1",
        outcome_name="YES",
        packet_id="pkt-case-yes",
        fair_value_estimate=Decimal("0.58"),
    )
    record_no = _build_record(
        condition_id="0xCASE2",
        token_id="999",
        market_slug="m-case-2",
        outcome_name="NO",
        packet_id="pkt-case-no",
        fair_value_estimate=Decimal("0.42"),
    )
    journal_path = _write_journal(tmp_path, [record_yes, record_no])
    client = FakeGammaClient(
        [
            # "True"/"False" are alternate YES/NO aliases in the Gamma labels.
            {
                "conditionId": "0xCASE1",
                "outcomes": ["True", "False"],
                "outcomePrices": ["1", "0"],
                "closed": True,
                "active": False,
            },
            {
                "conditionId": "0xCASE2",
                "outcomes": ["True", "False"],
                "outcomePrices": ["0", "1"],
                "closed": True,
                "active": False,
            },
        ]
    )

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.resolved_count == 2
    by_token = {obs.token_id: obs for obs in report.observations}
    # YES leg (alias "yes") vs winning "True" (alias "yes") -> won -> 1.
    assert by_token["888"].actual_outcome_value == Decimal("1")
    # NO leg (alias "no") vs winning "False" (alias "no") -> won -> 1.
    assert by_token["999"].actual_outcome_value == Decimal("1")


def test_outcome_prices_read_from_json_string_payload_not_resolution_status(tmp_path):
    # CRITICAL #1: Gamma sometimes returns outcomes/outcomePrices as
    # JSON-encoded STRINGS ('["Yes","No"]'). The tracker must decode them and
    # derive the winner, ignoring resolutionStatus entirely.
    record = _build_record(
        condition_id="0xJSON",
        token_id="101",
        market_slug="m-json",
        outcome_name="YES",
        packet_id="pkt-json",
        fair_value_estimate=Decimal("0.57"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient(
        [
            {
                "conditionId": "0xJSON",
                "outcomes": '["Yes","No"]',  # JSON string
                "outcomePrices": '["1","0"]',  # JSON string
                "closed": True,
                "active": False,
                "resolutionStatus": None,  # proves winner is NOT read from here
            }
        ]
    )

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.resolved_count == 1
    assert report.observations[0].actual_outcome_value == Decimal("1")


def test_resolution_status_yes_is_ignored_when_outcome_prices_say_no_won(tmp_path):
    # CRITICAL #1 stress test: resolutionStatus lies ("Yes") but outcomePrices
    # truthfully encode NO won (["0","1"]). The tracker MUST follow
    # outcomePrices and report the NO leg as the winner.
    record = _build_record(
        condition_id="0xLIE",
        token_id="102",
        market_slug="m-lie",
        outcome_name="NO",
        packet_id="pkt-lie",
        fair_value_estimate=Decimal("0.30"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient(
        [
            {
                "conditionId": "0xLIE",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0", "1"],  # NO actually won
                "closed": True,
                "active": False,
                "resolutionStatus": "Yes",  # misleading; must be ignored
            }
        ]
    )

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    observation = report.observations[0]
    # NO leg won per outcomePrices -> actual = 1, regardless of resolutionStatus.
    assert observation.actual_outcome_value == Decimal("1")


def test_pending_when_closed_but_outcome_prices_ambiguous_tie(tmp_path):
    # Closed market but outcomePrices tied (["0.5","0.5"]) -> no clear winner
    # -> PENDING (never silently treated as resolved).
    record = _build_record(
        condition_id="0xTIE",
        token_id="103",
        market_slug="m-tie",
        outcome_name="YES",
        packet_id="pkt-tie",
        fair_value_estimate=Decimal("0.50"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient(
        [
            {
                "conditionId": "0xTIE",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.5", "0.5"],
                "closed": True,
                "active": False,
            }
        ]
    )

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.resolved_count == 0
    assert report.pending_count == 1
    assert report.observations == ()


def test_pending_when_outcome_label_not_yes_or_no_alias(tmp_path):
    # Multi-outcome / unrecognized label ("Option A") -> cannot classify ->
    # PENDING. Binary alias matching is the contract.
    record = _build_record(
        condition_id="0xMULTI",
        token_id="104",
        market_slug="m-multi",
        outcome_name="YES",
        packet_id="pkt-multi",
        fair_value_estimate=Decimal("0.55"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient(
        [
            {
                "conditionId": "0xMULTI",
                "outcomes": ["Option A", "Option B"],
                "outcomePrices": ["1", "0"],
                "closed": True,
                "active": False,
            }
        ]
    )

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.resolved_count == 0
    assert report.pending_count == 1


def test_empty_journal_produces_empty_report_with_no_evidence(tmp_path):
    journal_path = _write_journal(tmp_path, [])
    client = FakeGammaClient([])

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.total_markets_checked == 0
    assert report.resolved_count == 0
    assert report.pending_count == 0
    assert report.observations == ()
    assert report.forecast_evidence_report is None
    assert report.paper_only is True
    assert report.report_only is True


def test_mixed_resolved_and_pending_legs_in_one_run(tmp_path):
    resolved_yes = _build_record(
        condition_id="0xR1",
        token_id="201",
        market_slug="m-r1",
        outcome_name="YES",
        packet_id="pkt-r1",
        fair_value_estimate=Decimal("0.65"),
    )
    pending_open = _build_record(
        condition_id="0xP1",
        token_id="202",
        market_slug="m-p1",
        outcome_name="YES",
        packet_id="pkt-p1",
        fair_value_estimate=Decimal("0.50"),
    )
    pending_missing = _build_record(
        condition_id="0xP2",
        token_id="203",
        market_slug="m-p2",
        outcome_name="NO",
        packet_id="pkt-p2",
        fair_value_estimate=Decimal("0.50"),
    )
    journal_path = _write_journal(tmp_path, [resolved_yes, pending_open, pending_missing])
    client = FakeGammaClient(
        [
            _yes_won_payload("0xR1"),
            {
                "conditionId": "0xP1",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.50", "0.50"],
                "closed": False,
                "active": True,
            },
            # 0xP2 intentionally absent from the closed slice.
        ]
    )

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.total_markets_checked == 3
    assert report.resolved_count == 1
    assert report.pending_count == 2
    assert len(report.observations) == 1
    assert report.observations[0].actual_outcome_value == Decimal("1")


def test_report_hard_enforces_resolved_equals_observation_count():
    with pytest.raises(ValueError, match="resolved_count must equal"):
        OutcomeTrackingReport(
            generated_at=GENERATED_AT,
            config_version="outcome-tracker-v1",
            total_markets_checked=2,
            resolved_count=2,
            pending_count=0,
            observations=(),  # mismatch: resolved_count=2 but 0 observations
            forecast_evidence_report=None,
        )


def test_report_hard_enforces_resolved_plus_pending_equals_total():
    with pytest.raises(ValueError, match="resolved_count \\+ pending_count"):
        OutcomeTrackingReport(
            generated_at=GENERATED_AT,
            config_version="outcome-tracker-v1",
            total_markets_checked=2,
            resolved_count=1,
            pending_count=2,  # 1 + 2 != 2
            observations=(),
            forecast_evidence_report=None,
        )


def test_report_hard_enforces_no_evidence_report_when_zero_observations():
    with pytest.raises(ValueError, match="forecast_evidence_report must be None"):
        # Construct a minimal real report to attach (0 observations -> status
        # incomplete_data). build_paper_forecast_evidence_report with () yields
        # such a report, so reuse it rather than hand-rolling one.
        from polymarket_alpha_lab.forecast_evidence import (
            PaperForecastEvidenceConfig,
            build_paper_forecast_evidence_report,
        )

        empty_evidence = build_paper_forecast_evidence_report(
            (),
            config=PaperForecastEvidenceConfig(config_version="outcome-tracker-v1"),
            generated_at=GENERATED_AT,
        )
        OutcomeTrackingReport(
            generated_at=GENERATED_AT,
            config_version="outcome-tracker-v1",
            total_markets_checked=0,
            resolved_count=0,
            pending_count=0,
            observations=(),
            forecast_evidence_report=empty_evidence,  # forbidden when 0 obs
        )


def test_report_hard_enforces_paper_and_report_only_with_is():
    # paper_only=False is rejected by the ``is True`` guard.
    with pytest.raises(ValueError, match="paper_only must be True"):
        OutcomeTrackingReport(
            generated_at=GENERATED_AT,
            config_version="outcome-tracker-v1",
            total_markets_checked=0,
            resolved_count=0,
            pending_count=0,
            observations=(),
            forecast_evidence_report=None,
            paper_only=False,
        )
    # paper_only=1 (truthy but not True) must be rejected (``is`` semantics,
    # not truthiness) so no coerced bool can satisfy the paper-only boundary.
    with pytest.raises(ValueError, match="paper_only must be True"):
        OutcomeTrackingReport(
            generated_at=GENERATED_AT,
            config_version="outcome-tracker-v1",
            total_markets_checked=0,
            resolved_count=0,
            pending_count=0,
            observations=(),
            forecast_evidence_report=None,
            paper_only=1,  # type: ignore[arg-type]
        )
    # report_only=1 (truthy but not True) is likewise rejected.
    with pytest.raises(ValueError, match="report_only must be True"):
        OutcomeTrackingReport(
            generated_at=GENERATED_AT,
            config_version="outcome-tracker-v1",
            total_markets_checked=0,
            resolved_count=0,
            pending_count=0,
            observations=(),
            forecast_evidence_report=None,
            report_only=1,  # type: ignore[arg-type]
        )


def test_check_outcomes_rejects_non_protocol_client(tmp_path):
    journal_path = _write_journal(tmp_path, [])
    # A bare object does not structurally satisfy OutcomeTrackerClient
    # (no list_markets method) -> the runtime_checkable Protocol guard rejects.
    with pytest.raises(ValueError, match="client must be an OutcomeTrackerClient"):
        check_outcomes(
            client=object(),  # type: ignore[arg-type]
            journal_path=journal_path,
            config=OutcomeTrackingConfig(),
            generated_at=GENERATED_AT,
        )


def test_check_outcomes_rejects_non_config_and_non_datetime(tmp_path):
    journal_path = _write_journal(tmp_path, [])
    client = FakeGammaClient([])
    with pytest.raises(ValueError, match="config must be an OutcomeTrackingConfig"):
        check_outcomes(
            client=client,
            journal_path=journal_path,
            config="not-a-config",  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        check_outcomes(
            client=client,
            journal_path=journal_path,
            config=OutcomeTrackingConfig(),
            generated_at="2026-06-16",  # type: ignore[arg-type]
        )


def test_closest_to_one_fallback_resolves_near_resolution_prices(tmp_path):
    # Closed market where outcomePrices is ["0.9999","0.0001"] (no exact "1"):
    # the closest-to-1 fallback should still declare index 0 the winner.
    record = _build_record(
        condition_id="0xNEAR",
        token_id="301",
        market_slug="m-near",
        outcome_name="YES",
        packet_id="pkt-near",
        fair_value_estimate=Decimal("0.70"),
    )
    journal_path = _write_journal(tmp_path, [record])
    client = FakeGammaClient(
        [
            {
                "conditionId": "0xNEAR",
                "outcomes": ["Yes", "No"],
                "outcomePrices": ["0.9999", "0.0001"],
                "closed": True,
                "active": False,
            }
        ]
    )

    report = check_outcomes(
        client=client,
        journal_path=journal_path,
        config=OutcomeTrackingConfig(),
        generated_at=GENERATED_AT,
    )

    assert report.resolved_count == 1
    assert report.observations[0].actual_outcome_value == Decimal("1")
