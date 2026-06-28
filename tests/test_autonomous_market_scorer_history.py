"""Tests for the autonomous market scorer history reducer."""

from __future__ import annotations

from dataclasses import FrozenInstanceError
from datetime import UTC, datetime
from decimal import Decimal
from types import SimpleNamespace

import pytest


def _history_api():
    import polymarket_alpha_lab.autonomous_market_scorer_history as history

    return history


def _at(hour: int, minute: int = 0) -> datetime:
    return datetime(2026, 6, 25, hour, minute, tzinfo=UTC)


def _row(
    condition_id: str,
    market_slug: str,
    *,
    recommended_notional: Decimal = Decimal("0.000000"),
    reason_codes: tuple[str, ...] = (),
    score_status: str = "scored",
) -> SimpleNamespace:
    return SimpleNamespace(
        condition_id=condition_id,
        market_slug=market_slug,
        recommended_notional=recommended_notional,
        reason_codes=reason_codes,
        score_status=score_status,
    )


def _source_config(
    *,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> SimpleNamespace:
    return SimpleNamespace(
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    generated_at: datetime,
    *,
    gate_status: str = "pass",
    rows: tuple[SimpleNamespace, ...] = (),
    reason_codes: tuple[str, ...] = (),
    total_recommended_notional: Decimal | object | None = None,
    markets_scored: int | None = None,
    markets_skipped: int = 0,
    markets_blocked: int = 0,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
    config: SimpleNamespace | None = None,
) -> SimpleNamespace:
    if total_recommended_notional is None:
        total_recommended_notional = sum(
            (
                row.recommended_notional
                for row in rows
                if getattr(row, "score_status", "scored") == "scored"
            ),
            Decimal("0.000000"),
        )
    if markets_scored is None:
        markets_scored = sum(
            1 for row in rows if getattr(row, "score_status", "scored") == "scored"
        )

    values = {
        "generated_at": generated_at,
        "config_version": "autonomous-market-scorer-v0",
        "gate_status": gate_status,
        "markets_scored": markets_scored,
        "markets_skipped": markets_skipped,
        "markets_blocked": markets_blocked,
        "total_recommended_notional": total_recommended_notional,
        "score_rows": rows,
        "reason_codes": reason_codes,
        "paper_only": paper_only,
        "report_only": report_only,
        "readonly": readonly,
    }
    if config is not None:
        values["config"] = config
    return SimpleNamespace(**values)


def _history_report_kwargs(**overrides: object) -> dict[str, object]:
    values: dict[str, object] = {
        "generated_at": _at(12, 5),
        "config_version": "autonomous-market-scorer-history-v0",
        "source_report_count": 3,
        "first_generated_at": _at(10),
        "latest_generated_at": _at(12),
        "history_span_seconds": 7200,
        "latest_gate_status": "pass",
        "latest_gate_status_streak": 3,
        "recurring_market_slug_counts": (),
        "recurring_condition_id_counts": (),
        "recurring_reason_code_counts": (),
        "latest_candidate_count": 1,
        "average_candidate_count": Decimal("1.000000"),
        "latest_recommended_notional": Decimal("3.000000"),
        "total_recommended_notional": Decimal("9.000000"),
        "notional_delta": Decimal("2.000000"),
        "blocked_report_count": 0,
        "skipped_report_count": 0,
        "history_status": "stable",
        "recommended_next_step": "continue_monitoring",
        "reason_codes": ("autonomous_market_scorer_history_stable",),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return values


def test_history_reducer_summarizes_recurring_candidates_and_reasons() -> None:
    history = _history_api()

    reports = (
        _report(
            _at(10),
            rows=(
                _row(
                    "condition-alpha",
                    "alpha-market",
                    recommended_notional=Decimal("10.000000"),
                ),
                _row(
                    "condition-beta",
                    "beta-market",
                    recommended_notional=Decimal("5.000000"),
                ),
            ),
            reason_codes=("alpha_reason", "shared_reason"),
        ),
        _report(
            _at(11),
            rows=(
                _row(
                    "condition-alpha",
                    "alpha-market",
                    recommended_notional=Decimal("12.000000"),
                ),
                _row(
                    "condition-gamma",
                    "gamma-market",
                    recommended_notional=Decimal("7.000000"),
                ),
            ),
            reason_codes=("gamma_reason", "shared_reason"),
        ),
        _report(
            _at(12),
            rows=(
                _row(
                    "condition-alpha",
                    "alpha-market",
                    recommended_notional=Decimal("20.000000"),
                ),
                _row(
                    "condition-gamma",
                    "gamma-market",
                    recommended_notional=Decimal("6.000000"),
                ),
            ),
            reason_codes=("shared_reason", "stable_reason"),
        ),
    )

    report = history.build_autonomous_market_scorer_history_report(
        reports,
        generated_at=_at(12, 10),
        config=history.AutonomousMarketScorerHistoryConfig(
            min_report_count=3,
            max_latest_age_seconds=3600,
        ),
    )

    assert report.generated_at == _at(12, 10)
    assert report.config_version == "autonomous-market-scorer-history-v0"
    assert report.source_report_count == 3
    assert report.first_generated_at == _at(10)
    assert report.latest_generated_at == _at(12)
    assert report.history_span_seconds == 7200
    assert report.latest_gate_status == "pass"
    assert report.latest_gate_status_streak == 3
    assert report.recurring_market_slug_counts == (
        history.AutonomousMarketScorerHistoryMarketSlugCount("alpha-market", 3),
        history.AutonomousMarketScorerHistoryMarketSlugCount("gamma-market", 2),
    )
    assert report.recurring_condition_id_counts == (
        history.AutonomousMarketScorerHistoryConditionIdCount("condition-alpha", 3),
        history.AutonomousMarketScorerHistoryConditionIdCount("condition-gamma", 2),
    )
    assert report.recurring_reason_code_counts == (
        history.AutonomousMarketScorerHistoryReasonCodeCount("shared_reason", 3),
    )
    assert report.latest_candidate_count == 2
    assert report.average_candidate_count == Decimal("2.000000")
    assert report.latest_recommended_notional == Decimal("26.000000")
    assert report.total_recommended_notional == Decimal("60.000000")
    assert report.notional_delta == Decimal("11.000000")
    assert report.blocked_report_count == 0
    assert report.skipped_report_count == 0
    assert report.history_status == "stable"
    assert report.recommended_next_step == "continue_monitoring"
    assert report.reason_codes == (
        "alpha_reason",
        "autonomous_market_scorer_history_stable",
        "gamma_reason",
        "shared_reason",
        "stable_reason",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_history_reducer_requires_non_empty_inputs() -> None:
    history = _history_api()

    with pytest.raises(ValueError, match="non-empty"):
        history.build_autonomous_market_scorer_history_report(
            (),
            generated_at=_at(12),
        )


def test_history_reducer_marks_insufficient_history() -> None:
    history = _history_api()

    report = history.build_autonomous_market_scorer_history_report(
        (
            _report(
                _at(12),
                rows=(
                    _row(
                        "condition-alpha",
                        "alpha-market",
                        recommended_notional=Decimal("3.000000"),
                    ),
                ),
                reason_codes=("alpha_reason",),
            ),
        ),
        generated_at=_at(12, 5),
        config=history.AutonomousMarketScorerHistoryConfig(min_report_count=2),
    )

    assert report.history_status == "insufficient_history"
    assert report.recommended_next_step == "collect_more_scorer_history"
    assert report.reason_codes == (
        "alpha_reason",
        "autonomous_market_scorer_history_insufficient_history",
    )


def test_history_reducer_counts_blocked_and_skipped_prevalence() -> None:
    history = _history_api()

    report = history.build_autonomous_market_scorer_history_report(
        (
            _report(
                _at(10),
                gate_status="watch",
                rows=(
                    _row(
                        "condition-alpha",
                        "alpha-market",
                        recommended_notional=Decimal("4.000000"),
                    ),
                ),
                markets_skipped=1,
            ),
            _report(
                _at(11),
                gate_status="blocked",
                rows=(),
                markets_scored=0,
                markets_blocked=1,
                total_recommended_notional=Decimal("0.000000"),
                reason_codes=("gate_blocked",),
            ),
            _report(
                _at(12),
                rows=(
                    _row(
                        "condition-beta",
                        "beta-market",
                        recommended_notional=Decimal("9.000000"),
                    ),
                ),
                markets_skipped=1,
            ),
        ),
        generated_at=_at(12, 5),
        config=history.AutonomousMarketScorerHistoryConfig(
            min_report_count=3,
            max_blocked_report_count=0,
        ),
    )

    assert report.blocked_report_count == 1
    assert report.skipped_report_count == 2
    assert report.history_status == "blocked"
    assert report.recommended_next_step == "review_scorer_inputs"
    assert report.reason_codes == (
        "autonomous_market_scorer_history_blocked",
        "gate_blocked",
    )


def test_history_reducer_marks_stale_latest_report_for_review() -> None:
    history = _history_api()

    report = history.build_autonomous_market_scorer_history_report(
        (
            _report(_at(10), rows=(_row("condition-a", "a-market"),)),
            _report(_at(11), rows=(_row("condition-b", "b-market"),)),
            _report(_at(12), rows=(_row("condition-c", "c-market"),)),
        ),
        generated_at=_at(12, 10),
        config=history.AutonomousMarketScorerHistoryConfig(
            min_report_count=3,
            max_latest_age_seconds=60,
        ),
    )

    assert report.history_status == "stale"
    assert report.recommended_next_step == "review_scorer_inputs"
    assert report.reason_codes == ("autonomous_market_scorer_history_stale",)


def test_history_reducer_marks_no_latest_candidates_for_review() -> None:
    history = _history_api()

    report = history.build_autonomous_market_scorer_history_report(
        (
            _report(_at(10), rows=(_row("condition-a", "a-market"),)),
            _report(_at(11), rows=(_row("condition-b", "b-market"),)),
            _report(
                _at(12),
                gate_status="watch",
                rows=(),
                markets_scored=0,
                markets_skipped=1,
                total_recommended_notional=Decimal("0.000000"),
            ),
        ),
        generated_at=_at(12, 5),
        config=history.AutonomousMarketScorerHistoryConfig(min_report_count=3),
    )

    assert report.latest_candidate_count == 0
    assert report.history_status == "no_candidates"
    assert report.recommended_next_step == "review_scorer_inputs"
    assert report.reason_codes == (
        "autonomous_market_scorer_history_no_candidates",
    )


def test_history_reducer_rejects_non_chronological_inputs() -> None:
    history = _history_api()

    with pytest.raises(ValueError, match="chronological"):
        history.build_autonomous_market_scorer_history_report(
            (
                _report(_at(12), rows=(_row("condition-a", "a-market"),)),
                _report(_at(11), rows=(_row("condition-b", "b-market"),)),
            ),
            generated_at=_at(12, 5),
        )


def test_history_reducer_rejects_float_notional_inputs() -> None:
    history = _history_api()

    with pytest.raises(ValueError, match="total_recommended_notional.*Decimal"):
        history.build_autonomous_market_scorer_history_report(
            (
                _report(
                    _at(10),
                    rows=(_row("condition-a", "a-market"),),
                    total_recommended_notional=Decimal("1.000000"),
                ),
                _report(
                    _at(11),
                    rows=(_row("condition-b", "b-market"),),
                    total_recommended_notional=1.5,
                ),
            ),
            generated_at=_at(11, 5),
            config=history.AutonomousMarketScorerHistoryConfig(min_report_count=2),
        )


def test_history_reducer_rejects_row_level_float_recommended_notional() -> None:
    history = _history_api()

    with pytest.raises(ValueError, match="score_rows recommended_notional.*Decimal"):
        history.build_autonomous_market_scorer_history_report(
            (
                _report(
                    _at(10),
                    rows=(
                        _row(
                            "condition-a",
                            "a-market",
                            recommended_notional=Decimal("1.000000"),
                        ),
                    ),
                    total_recommended_notional=Decimal("1.000000"),
                ),
                _report(
                    _at(11),
                    rows=(
                        _row(
                            "condition-b",
                            "b-market",
                            recommended_notional=1.5,
                        ),
                    ),
                    total_recommended_notional=Decimal("1.500000"),
                ),
            ),
            generated_at=_at(11, 5),
            config=history.AutonomousMarketScorerHistoryConfig(min_report_count=2),
        )


def test_history_reducer_derives_missing_report_notional_from_rows() -> None:
    history = _history_api()

    reports = (
        SimpleNamespace(
            generated_at=_at(10),
            gate_status="pass",
            score_rows=(
                _row(
                    "condition-alpha",
                    "alpha-market",
                    recommended_notional=Decimal("2.500000"),
                ),
            ),
            reason_codes=(),
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
        SimpleNamespace(
            generated_at=_at(11),
            gate_status="pass",
            score_rows=(
                _row(
                    "condition-alpha",
                    "alpha-market",
                    recommended_notional=Decimal("4.000000"),
                ),
                _row(
                    "condition-skipped",
                    "skipped-market",
                    recommended_notional=Decimal("100.000000"),
                    score_status="skipped",
                ),
            ),
            reason_codes=(),
            paper_only=True,
            report_only=True,
            readonly=True,
        ),
    )

    report = history.build_autonomous_market_scorer_history_report(
        reports,
        generated_at=_at(11, 5),
        config=history.AutonomousMarketScorerHistoryConfig(min_report_count=2),
    )

    assert report.latest_candidate_count == 1
    assert report.latest_recommended_notional == Decimal("4.000000")
    assert report.total_recommended_notional == Decimal("6.500000")
    assert report.notional_delta == Decimal("1.500000")


def test_history_reducer_uses_row_reason_codes_when_report_reasons_are_empty() -> None:
    history = _history_api()

    report = history.build_autonomous_market_scorer_history_report(
        (
            _report(
                _at(10),
                rows=(
                    _row(
                        "condition-alpha",
                        "alpha-market",
                        reason_codes=("shared_row_reason",),
                    ),
                ),
            ),
            _report(
                _at(11),
                rows=(
                    _row(
                        "condition-alpha",
                        "alpha-market",
                        reason_codes=("shared_row_reason",),
                    ),
                ),
            ),
        ),
        generated_at=_at(11, 5),
        config=history.AutonomousMarketScorerHistoryConfig(min_report_count=2),
    )

    assert report.recurring_reason_code_counts == (
        history.AutonomousMarketScorerHistoryReasonCodeCount(
            "shared_row_reason",
            2,
        ),
    )
    assert report.reason_codes == (
        "autonomous_market_scorer_history_stable",
        "shared_row_reason",
    )


def test_history_config_and_sources_reject_false_hard_flags() -> None:
    history = _history_api()

    with pytest.raises(ValueError, match="paper_only"):
        history.AutonomousMarketScorerHistoryConfig(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        history.build_autonomous_market_scorer_history_report(
            (
                _report(
                    _at(10),
                    rows=(_row("condition-a", "a-market"),),
                    report_only=False,
                ),
            ),
            generated_at=_at(10, 5),
        )

    with pytest.raises(ValueError, match="readonly"):
        history.build_autonomous_market_scorer_history_report(
            (
                _report(
                    _at(10),
                    rows=(_row("condition-a", "a-market"),),
                    config=_source_config(readonly=False),
                ),
            ),
            generated_at=_at(10, 5),
        )


@pytest.mark.parametrize(
    "field_name",
    (
        "average_candidate_count",
        "latest_recommended_notional",
        "total_recommended_notional",
        "notional_delta",
    ),
)
@pytest.mark.parametrize(
    "non_finite_value",
    (
        Decimal("NaN"),
        Decimal("Infinity"),
        Decimal("-Infinity"),
    ),
)
def test_history_report_rejects_non_finite_decimal_fields(
    field_name: str,
    non_finite_value: Decimal,
) -> None:
    history = _history_api()

    with pytest.raises(ValueError, match=rf"{field_name}.*finite"):
        history.AutonomousMarketScorerHistoryReport(
            **_history_report_kwargs(**{field_name: non_finite_value}),
        )


@pytest.mark.parametrize(
    "class_name",
    (
        "AutonomousMarketScorerHistoryConfig",
        "AutonomousMarketScorerHistoryMarketSlugCount",
        "AutonomousMarketScorerHistoryConditionIdCount",
        "AutonomousMarketScorerHistoryReasonCodeCount",
        "AutonomousMarketScorerHistoryReport",
    ),
)
def test_public_history_dataclasses_do_not_support_subclassing(
    class_name: str,
) -> None:
    history = _history_api()
    base_class = getattr(history, class_name)

    with pytest.raises(TypeError, match=rf"{class_name} .*subclassing"):
        type(
            f"Mutable{class_name}",
            (base_class,),
            {
                "__annotations__": {"mutable_extra": list},
                "mutable_extra": [],
            },
        )


def test_history_dataclasses_are_frozen() -> None:
    history = _history_api()

    config = history.AutonomousMarketScorerHistoryConfig()
    with pytest.raises(FrozenInstanceError):
        config.min_report_count = 4

    count = history.AutonomousMarketScorerHistoryReasonCodeCount(
        "shared_reason",
        2,
    )
    with pytest.raises(FrozenInstanceError):
        count.report_count = 3

    report = history.build_autonomous_market_scorer_history_report(
        (
            _report(_at(10), rows=(_row("condition-a", "a-market"),)),
            _report(_at(11), rows=(_row("condition-b", "b-market"),)),
            _report(_at(12), rows=(_row("condition-c", "c-market"),)),
        ),
        generated_at=_at(12, 5),
    )
    with pytest.raises(FrozenInstanceError):
        report.history_status = "changed"
