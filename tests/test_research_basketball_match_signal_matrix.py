from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_basketball_match_signal_matrix import (
    DEFAULT_RESEARCH_BASKETBALL_MATCH_SIGNAL_MATRIX_CONFIG_VERSION,
    ResearchBasketballMatchSignalMatrixConfig,
    ResearchBasketballMatchSignalMatrixObservation,
    ResearchBasketballMatchSignalMatrixReasonCodeCount,
    ResearchBasketballMatchSignalMatrixReport,
    ResearchBasketballMatchSignalMatrixRow,
    build_research_basketball_match_signal_matrix_report,
    research_basketball_match_signal_matrix_digest,
    research_basketball_match_signal_matrix_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchBasketballMatchSignalMatrixConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_BASKETBALL_MATCH_SIGNAL_MATRIX_CONFIG_VERSION,
        "form_weight": d("0.220000"),
        "injury_weight": d("0.240000"),
        "schedule_weight": d("0.180000"),
        "home_away_weight": d("0.080000"),
        "book_depth_weight": d("0.160000"),
        "conflict_weight": d("0.120000"),
        "watch_priority_threshold": d("0.350000"),
        "block_priority_threshold": d("0.650000"),
        "injury_pressure_watch": d("0.350000"),
        "injury_pressure_block": d("0.700000"),
        "back_to_back_watch": d("0.500000"),
        "back_to_back_block": d("0.800000"),
        "book_depth_watch": d("0.400000"),
        "book_depth_block": d("0.750000"),
        "conflict_watch": d("0.300000"),
        "conflict_block": d("0.600000"),
        "fresh_information_max_age_seconds": d("7200.000000"),
        "stale_information_block_age_seconds": d("43200.000000"),
    }
    values.update(overrides)
    return ResearchBasketballMatchSignalMatrixConfig(**values)


def observation(
    public_match_label: str = "alpha-vs-beta-home",
    *,
    league: str = "pro-basketball",
    team_label: str = "Alpha",
    opponent_label: str = "Beta",
    team_side: str = "home",
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    team_form_score: Decimal = d("0.850000"),
    injury_pressure_score: Decimal = d("0.100000"),
    back_to_back_pressure_score: Decimal = d("0.100000"),
    rest_travel_pressure_score: Decimal = d("0.100000"),
    home_away_context_score: Decimal = d("0.100000"),
    book_depth_gap_score: Decimal = d("0.100000"),
    line_signal_conflict_score: Decimal = d("0.000000"),
    support_signal_count: Decimal = d("4.000000"),
    reason_codes: tuple[str, ...] = ("basketball_match_signal_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchBasketballMatchSignalMatrixObservation:
    return ResearchBasketballMatchSignalMatrixObservation(
        public_match_label=public_match_label,
        league=league,
        team_label=team_label,
        opponent_label=opponent_label,
        team_side=team_side,
        observed_at=observed_at,
        team_form_score=team_form_score,
        injury_pressure_score=injury_pressure_score,
        back_to_back_pressure_score=back_to_back_pressure_score,
        rest_travel_pressure_score=rest_travel_pressure_score,
        home_away_context_score=home_away_context_score,
        book_depth_gap_score=book_depth_gap_score,
        line_signal_conflict_score=line_signal_conflict_score,
        support_signal_count=support_signal_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchBasketballMatchSignalMatrixObservation,
    cfg: ResearchBasketballMatchSignalMatrixConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchBasketballMatchSignalMatrixReport:
    return build_research_basketball_match_signal_matrix_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if type(value) is dict:
        for key, item in value.items():
            values.extend(walk_payload_values(key))
            values.extend(walk_payload_values(item))
    elif type(value) is list:
        for item in value:
            values.extend(walk_payload_values(item))
    return tuple(values)


def test_pass_watch_block_rollups_use_public_statuses_only() -> None:
    matrix_report = report(
        observation("pass-home", team_label="Alpha"),
        observation(
            "watch-away",
            team_label="Bravo",
            team_side="away",
            team_form_score=d("0.520000"),
            injury_pressure_score=d("0.250000"),
            back_to_back_pressure_score=d("0.620000"),
            book_depth_gap_score=d("0.300000"),
        ),
        observation(
            "block-neutral",
            team_label="Charlie",
            team_side="neutral",
            team_form_score=d("0.150000"),
            injury_pressure_score=d("0.720000"),
            back_to_back_pressure_score=d("0.900000"),
            rest_travel_pressure_score=d("0.800000"),
            book_depth_gap_score=d("0.800000"),
            line_signal_conflict_score=d("0.650000"),
        ),
    )
    payload = research_basketball_match_signal_matrix_payload(matrix_report)

    assert matrix_report.status == "block"
    assert matrix_report.subject_count == d("3.000000")
    assert matrix_report.pass_count == d("1.000000")
    assert matrix_report.watch_count == d("1.000000")
    assert matrix_report.block_count == d("1.000000")
    assert matrix_report.hard_flag_count == d("1.000000")
    assert tuple(row.public_status for row in matrix_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert {row["status"] for row in payload["rows"]} == {"pass", "watch", "block"}
    assert "blocked" not in json.dumps(payload, sort_keys=True)


def test_clear_report_payload_is_decimal_stringed_and_not_advice() -> None:
    matrix_report = report(observation("match-clear"))
    payload = research_basketball_match_signal_matrix_payload(matrix_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert matrix_report.status == "pass"
    assert matrix_report.reason_codes == ("basketball_match_signal_matrix_pass",)
    assert matrix_report.average_research_priority_score == d("0.095000")
    assert matrix_report.max_research_priority_score == d("0.095000")
    assert matrix_report.average_information_age_seconds == d("3600.000000")
    assert matrix_report.digest.startswith("basketball-match-signal-matrix-v0:")
    assert research_basketball_match_signal_matrix_digest(matrix_report) == (
        matrix_report.digest
    )

    row = matrix_report.rows[0]
    assert type(row) is ResearchBasketballMatchSignalMatrixRow
    assert row.public_match_label == "match-clear"
    assert row.status == "pass"
    assert row.public_status == "pass"
    assert row.information_age_seconds == d("3600.000000")
    assert row.freshness_score == d("1.000000")
    assert row.research_priority_score == d("0.095000")
    assert row.hard_flag is False
    assert row.reason_codes == (
        "basketball_match_signal_input_available",
        "basketball_match_signal_matrix_pass",
        "book_depth_signal_clear",
        "conflict_signal_clear",
        "fresh_information",
        "injury_signal_clear",
        "schedule_signal_clear",
    )

    assert payload["subject_count"] == "1.000000"
    assert payload["rows"][0]["research_priority_score"] == "0.095000"
    assert payload["digest"] == matrix_report.digest
    assert payload["rows"][0]["digest"] == row.digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk_payload_values(payload))
    for unsafe_text in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_ref",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert unsafe_text not in encoded.lower()


def test_empty_inputs_block_without_rows_and_with_digest() -> None:
    matrix_report = report()

    assert matrix_report.status == "block"
    assert matrix_report.subject_count == ZERO
    assert matrix_report.pass_count == ZERO
    assert matrix_report.watch_count == ZERO
    assert matrix_report.block_count == ZERO
    assert matrix_report.reason_codes == ("basketball_match_signal_matrix_no_inputs",)
    assert matrix_report.reason_code_counts == (
        ResearchBasketballMatchSignalMatrixReasonCodeCount(
            reason_code="basketball_match_signal_matrix_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert matrix_report.rows == ()
    assert matrix_report.digest.startswith("basketball-match-signal-matrix-v0:")


def test_decimal_type_rejection_and_datetime_normalization() -> None:
    shifted = report(
        observation(
            observed_at=datetime(
                2026,
                7,
                8,
                11,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
    )
    assert shifted.rows[0].observed_at == GENERATED_AT
    assert shifted.rows[0].information_age_seconds == ZERO

    with pytest.raises(ValueError, match="team_form_score"):
        observation(team_form_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="injury_pressure_score"):
        observation(injury_pressure_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="book_depth_gap_score"):
        observation(book_depth_gap_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            observation(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 18, 0, tzinfo=_NoneOffsetTimezone()))


def test_public_leak_rejection_and_hard_flags() -> None:
    matrix_report = report(observation("hard-flags"))

    assert is_dataclass(ResearchBasketballMatchSignalMatrixConfig)
    assert is_dataclass(ResearchBasketballMatchSignalMatrixObservation)
    assert is_dataclass(ResearchBasketballMatchSignalMatrixRow)
    assert is_dataclass(ResearchBasketballMatchSignalMatrixReasonCodeCount)
    assert is_dataclass(ResearchBasketballMatchSignalMatrixReport)
    with pytest.raises(FrozenInstanceError):
        matrix_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        matrix_report.rows[0].research_priority_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(matrix_report, readonly=False)

    for kwargs in (
        {"public_match_label": "raw_candidate_123"},
        {"public_match_label": "market_slug-finals"},
        {"team_label": "contains source_url field"},
        {"opponent_label": "wallet order flow"},
        {"league": "recommendation desk"},
        {"reason_codes": ("buy_signal",)},
    ):
        with pytest.raises(ValueError, match="unsafe|sensitive"):
            observation(**kwargs)


def test_hard_flags_drive_block_status_and_reason_counts() -> None:
    matrix_report = report(
        observation(
            "injury-block",
            team_form_score=d("0.600000"),
            injury_pressure_score=d("0.720000"),
            back_to_back_pressure_score=d("0.400000"),
            book_depth_gap_score=d("0.300000"),
        ),
        observation(
            "stale-watch",
            team_form_score=d("0.700000"),
            injury_pressure_score=d("0.200000"),
            back_to_back_pressure_score=d("0.300000"),
            book_depth_gap_score=d("0.250000"),
            observed_at=GENERATED_AT - timedelta(hours=4),
        ),
    )

    assert matrix_report.status == "block"
    assert matrix_report.hard_flag_count == d("1.000000")
    assert matrix_report.stale_information_count == d("1.000000")
    assert matrix_report.injury_concern_count == d("1.000000")
    assert matrix_report.schedule_congestion_count == d("0.000000")
    assert matrix_report.book_depth_concern_count == d("0.000000")
    assert matrix_report.rows[0].public_match_label == "injury-block"
    assert matrix_report.rows[0].public_status == "block"
    assert matrix_report.rows[0].hard_flag is True
    assert "injury_signal_block" in matrix_report.rows[0].reason_codes
    assert matrix_report.rows[1].public_status == "watch"
    assert "information_age_watch" in matrix_report.rows[1].reason_codes
    assert (
        ResearchBasketballMatchSignalMatrixReasonCodeCount(
            reason_code="basketball_match_signal_input_available",
            count=d("2.000000"),
        )
        in matrix_report.reason_code_counts
    )


def test_deterministic_payload_and_report_digest_consistency() -> None:
    first = report(
        observation(
            "z-watch",
            team_label="Zulu",
            back_to_back_pressure_score=d("0.600000"),
            injury_pressure_score=d("0.200000"),
            book_depth_gap_score=d("0.200000"),
        ),
        observation(
            "a-block",
            team_label="Alpha",
            team_form_score=d("0.100000"),
            injury_pressure_score=d("0.800000"),
            back_to_back_pressure_score=d("0.900000"),
            book_depth_gap_score=d("0.800000"),
        ),
        observation("m-pass", team_label="Mike"),
    )
    second = report(
        observation("m-pass", team_label="Mike"),
        observation(
            "a-block",
            team_label="Alpha",
            team_form_score=d("0.100000"),
            injury_pressure_score=d("0.800000"),
            back_to_back_pressure_score=d("0.900000"),
            book_depth_gap_score=d("0.800000"),
        ),
        observation(
            "z-watch",
            team_label="Zulu",
            back_to_back_pressure_score=d("0.600000"),
            injury_pressure_score=d("0.200000"),
            book_depth_gap_score=d("0.200000"),
        ),
    )

    assert first.rows == second.rows
    assert first.digest == second.digest
    assert research_basketball_match_signal_matrix_payload(first) == (
        research_basketball_match_signal_matrix_payload(second)
    )
    assert research_basketball_match_signal_matrix_digest(first) == first.digest

    object.__setattr__(first.rows[0], "research_priority_score", d("0.000000"))
    with pytest.raises(ValueError, match="digest|research_priority_score"):
        research_basketball_match_signal_matrix_payload(first)


def test_report_rejects_inconsistent_public_counts_and_unsupported_statuses() -> None:
    matrix_report = report(observation("consistent"))

    with pytest.raises(ValueError, match="subject_count"):
        replace(matrix_report, subject_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(matrix_report, status="blocked")
    with pytest.raises(ValueError, match="average_research_priority_score"):
        replace(matrix_report, average_research_priority_score=d("9.000000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(matrix_report, reason_code_counts=())

    with pytest.raises(ValueError, match="ResearchBasketballMatchSignalMatrixReport"):
        research_basketball_match_signal_matrix_payload(
            {"paper_only": True, "report_only": True, "readonly": True},
        )  # type: ignore[arg-type]


def test_public_dataclasses_reject_subclassing_and_numeric_public_fields_are_decimal() -> None:
    matrix_report = report(observation("exact"))
    public_values = (
        config(),
        observation("exact-input"),
        matrix_report.rows[0],
        matrix_report.reason_code_counts[0],
        matrix_report,
    )

    for value in public_values:
        public_type = type(value)
        kwargs = {field.name: getattr(value, field.name) for field in fields(value)}
        with pytest.raises(TypeError, match="does not support subclassing"):
            type(f"{public_type.__name__}Subclass", (public_type,), {})
        subclass = _make_subclass_bypassing_final_guard(public_type)
        with pytest.raises(ValueError, match="must be exactly"):
            subclass(**kwargs)
        for field in fields(value):
            item = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly", "hard_flag"}:
                continue
            assert type(item) is not int
            assert type(item) is not float


def _make_subclass_bypassing_final_guard(public_type: type[object]) -> type[object]:
    sentinel = object()
    original_init_subclass = public_type.__dict__.get("__init_subclass__", sentinel)
    public_type.__init_subclass__ = classmethod(lambda cls, **kwargs: None)  # type: ignore[attr-defined]
    try:
        return type(f"{public_type.__name__}BypassedSubclass", (public_type,), {})
    finally:
        if original_init_subclass is sentinel:
            delattr(public_type, "__init_subclass__")
        else:
            public_type.__init_subclass__ = original_init_subclass  # type: ignore[attr-defined]
