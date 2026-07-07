from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_catalyst_impact_scorer_report import (
    ResearchCatalystImpactEventInput,
    ResearchCatalystImpactReasonCodeCount,
    ResearchCatalystImpactScoreRow,
    ResearchCatalystImpactScorerConfig,
    ResearchCatalystImpactScorerReport,
    build_research_catalyst_impact_scorer_report,
    research_catalyst_impact_scorer_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedEventShape:
    event_id: str
    catalyst_kind: str
    time_until_event_minutes: Decimal
    time_until_settlement_minutes: Decimal
    confirmation_count: Decimal
    official_confirmation_score: Decimal
    impact_relevance_score: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchCatalystImpactScorerConfig:
    values = {
        "config_version": "research-catalyst-impact-scorer-report-v0",
        "pass_impact_score": d("0.700000"),
        "watch_impact_score": d("0.400000"),
        "min_confirmation_count": d("2"),
        "min_official_confirmation_score": d("0.600000"),
        "min_settlement_buffer_minutes": d("30"),
        "min_reaction_buffer_minutes": d("15"),
        "timing_weight": d("0.350000"),
        "confirmation_weight": d("0.250000"),
        "impact_weight": d("0.250000"),
        "settlement_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchCatalystImpactScorerConfig(**values)


def event(
    event_id: str = "policy-release",
    *,
    catalyst_kind: str = "policy_release",
    time_until_event_minutes: Decimal = d("60"),
    time_until_settlement_minutes: Decimal = d("1440"),
    confirmation_count: Decimal = d("2"),
    official_confirmation_score: Decimal = d("0.900000"),
    impact_relevance_score: Decimal = d("0.900000"),
    reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchCatalystImpactEventInput:
    return ResearchCatalystImpactEventInput(
        event_id=event_id,
        catalyst_kind=catalyst_kind,
        time_until_event_minutes=time_until_event_minutes,
        time_until_settlement_minutes=time_until_settlement_minutes,
        confirmation_count=confirmation_count,
        official_confirmation_score=official_confirmation_score,
        impact_relevance_score=impact_relevance_score,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    events: tuple[object, ...],
    *,
    cfg: ResearchCatalystImpactScorerConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchCatalystImpactScorerReport:
    return build_research_catalyst_impact_scorer_report(
        events,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_with_decimal_counts_and_no_rows() -> None:
    scorer_report = report(())

    assert type(scorer_report) is ResearchCatalystImpactScorerReport
    assert scorer_report.generated_at == GENERATED_AT
    assert scorer_report.config_version == "research-catalyst-impact-scorer-report-v0"
    assert scorer_report.event_count == d("0")
    assert scorer_report.pass_count == d("0")
    assert scorer_report.watch_count == d("0")
    assert scorer_report.block_count == d("0")
    assert scorer_report.average_impact_score is None
    assert scorer_report.status == "block"
    assert scorer_report.reason_codes == ("no_research_events",)
    assert scorer_report.reason_code_counts == (
        ResearchCatalystImpactReasonCodeCount(
            reason_code="no_research_events",
            count=d("1"),
        ),
    )
    assert scorer_report.rows == ()
    assert scorer_report.paper_only is True
    assert scorer_report.report_only is True
    assert scorer_report.readonly is True


def test_policy_macro_sports_company_chain_and_settlement_windows_score_statuses() -> None:
    scorer_report = report(
        (
            event(
                "sports-kickoff",
                catalyst_kind="sports_node",
                time_until_event_minutes=d("300"),
                time_until_settlement_minutes=d("120"),
                reason_codes=("manual_reviewed",),
            ),
            event(
                "macro-cpi",
                catalyst_kind="macro_data",
                time_until_event_minutes=d("30"),
                time_until_settlement_minutes=d("240"),
                confirmation_count=d("1"),
                official_confirmation_score=d("0.500000"),
                impact_relevance_score=d("0.600000"),
            ),
            event(
                "policy-release",
                catalyst_kind="policy_release",
                time_until_event_minutes=d("60"),
                time_until_settlement_minutes=d("1440"),
                confirmation_count=d("2"),
                official_confirmation_score=d("0.900000"),
                impact_relevance_score=d("0.900000"),
            ),
            SuppliedEventShape(
                event_id="company-earnings",
                catalyst_kind="company_event",
                time_until_event_minutes=d("60"),
                time_until_settlement_minutes=d("240"),
                confirmation_count=d("2"),
                official_confirmation_score=d("0.800000"),
                impact_relevance_score=d("0.800000"),
            ),
            event(
                "chain-upgrade",
                catalyst_kind="chain_event",
                time_until_event_minutes=d("60"),
                time_until_settlement_minutes=d("240"),
                confirmation_count=d("2"),
                official_confirmation_score=d("0.300000"),
                impact_relevance_score=d("0.800000"),
            ),
            event(
                "settlement-cutoff",
                catalyst_kind="settlement_window",
                time_until_event_minutes=d("30"),
                time_until_settlement_minutes=d("120"),
                confirmation_count=d("2"),
                official_confirmation_score=d("0.800000"),
                impact_relevance_score=d("0.800000"),
            ),
        ),
    )

    rows = {row.event_id: row for row in scorer_report.rows}

    assert tuple(rows) == (
        "chain-upgrade",
        "company-earnings",
        "macro-cpi",
        "policy-release",
        "settlement-cutoff",
        "sports-kickoff",
    )
    assert scorer_report.status == "block"
    assert scorer_report.event_count == d("6")
    assert scorer_report.pass_count == d("3")
    assert scorer_report.watch_count == d("2")
    assert scorer_report.block_count == d("1")
    assert scorer_report.average_impact_score == d("0.818750")

    assert rows["policy-release"].status == "pass"
    assert rows["policy-release"].impact_score == d("0.962500")
    assert "policy_release_timing_aligned" in rows["policy-release"].reason_codes

    assert rows["macro-cpi"].status == "watch"
    assert rows["macro-cpi"].impact_score == d("0.775000")
    assert "macro_data_timing_aligned" in rows["macro-cpi"].reason_codes
    assert "confirmation_below_threshold" in rows["macro-cpi"].reason_codes

    assert rows["sports-kickoff"].status == "block"
    assert rows["sports-kickoff"].impact_score == d("0.462500")
    assert "sports_node_after_settlement" in rows["sports-kickoff"].reason_codes
    assert "input_manual_reviewed" in rows["sports-kickoff"].reason_codes

    assert rows["company-earnings"].status == "pass"
    assert rows["company-earnings"].impact_score == d("0.925000")
    assert "company_event_timing_aligned" in rows["company-earnings"].reason_codes

    assert rows["chain-upgrade"].status == "watch"
    assert rows["chain-upgrade"].impact_score == d("0.862500")
    assert "chain_event_timing_aligned" in rows["chain-upgrade"].reason_codes
    assert "official_confirmation_low" in rows["chain-upgrade"].reason_codes

    assert rows["settlement-cutoff"].status == "pass"
    assert rows["settlement-cutoff"].impact_score == d("0.925000")
    assert "settlement_window_timing_aligned" in rows["settlement-cutoff"].reason_codes


def test_payload_is_json_ready_decimal_only_and_public_surface_safe() -> None:
    scorer_report = report(
        (
            event(
                "policy-release",
                catalyst_kind="policy_release",
                reason_codes=("analyst_checked",),
            ),
            event(
                "macro-cpi",
                catalyst_kind="macro_data",
                time_until_event_minutes=d("30"),
                time_until_settlement_minutes=d("240"),
                confirmation_count=d("1"),
                official_confirmation_score=d("0.500000"),
                impact_relevance_score=d("0.600000"),
            ),
        ),
    )

    payload = research_catalyst_impact_scorer_report_payload(scorer_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert scorer_report.payload == payload
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["impact_score"] == str(scorer_report.rows[0].impact_score)
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert _public_strings_are_safe(payload)


def test_validation_rejects_bad_types_unknown_kinds_unsafe_strings_and_flags() -> None:
    with pytest.raises(ValueError, match="timing_weight"):
        config(timing_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_impact_score"):
        config(pass_impact_score=0.7)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_impact_score"):
        config(watch_impact_score=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((event(),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="catalyst_kind"):
        event(catalyst_kind="weather")
    with pytest.raises(ValueError, match="time_until_event_minutes"):
        event(time_until_event_minutes=d("-1"))
    with pytest.raises(ValueError, match="confirmation_count"):
        event(confirmation_count=d("1.5"))
    with pytest.raises(ValueError, match="official_confirmation_score"):
        event(official_confirmation_score=d("1.1"))
    with pytest.raises(ValueError, match="impact_relevance_score"):
        event(impact_relevance_score=d("-0.1"))
    with pytest.raises(ValueError, match="event_id"):
        event(event_id="https://hidden.example/value")
    with pytest.raises(ValueError, match="reason_codes"):
        event(reason_codes=("buy_now",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(event(), paper_only=False)
    with pytest.raises(ValueError, match="events"):
        build_research_catalyst_impact_scorer_report(
            "not-events",  # type: ignore[arg-type]
            config=config(),
            generated_at=GENERATED_AT,
        )


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    scorer_report = report((event(),))
    row = scorer_report.rows[0]

    assert type(row) is ResearchCatalystImpactScoreRow
    with pytest.raises(FrozenInstanceError):
        scorer_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.impact_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="impact_score"):
        replace(row, impact_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(scorer_report, status="watch")
    with pytest.raises(TypeError):

        class BadEventInput(ResearchCatalystImpactEventInput):
            pass


def test_owned_module_has_no_io_execution_or_restricted_language_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_catalyst_impact_scorer_report.py"
    )
    module_source = module_path.read_text(encoding="utf-8").lower()
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
        "execute(",
        "insert ",
        "delete ",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "to_sql",
    )
    restricted_language = ("buy", "sell", "position", "recommend")

    assert all(term not in module_source for term in forbidden_terms)
    assert all(term not in module_source for term in restricted_language)


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


def _public_strings_are_safe(payload: object) -> bool:
    unsafe_fragments = (
        "raw",
        "candidate",
        "market",
        "source",
        "url",
        "dsn",
        "table",
        "token",
    )
    restricted_language = ("buy", "sell", "position", "recommend")

    def check(value: object) -> bool:
        if isinstance(value, dict):
            return all(
                check(str(key)) and check(item)
                for key, item in value.items()
            )
        if isinstance(value, list):
            return all(check(item) for item in value)
        if isinstance(value, str):
            lowered = value.lower()
            return not any(
                fragment in lowered
                for fragment in (*unsafe_fragments, *restricted_language)
            )
        return True

    return check(payload)
