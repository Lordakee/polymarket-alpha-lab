from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_sports_match_signal_matrix import (
    DEFAULT_RESEARCH_SPORTS_MATCH_SIGNAL_MATRIX_CONFIG_VERSION,
    ResearchSportsMatchSignalMatrixConfig,
    ResearchSportsMatchSignalMatrixObservation,
    ResearchSportsMatchSignalMatrixReasonCodeCount,
    ResearchSportsMatchSignalMatrixReport,
    ResearchSportsMatchSignalMatrixRow,
    build_research_sports_match_signal_matrix_report,
    research_sports_match_signal_matrix_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 15, 30, tzinfo=UTC)
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


def config(**overrides: object) -> ResearchSportsMatchSignalMatrixConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_SPORTS_MATCH_SIGNAL_MATRIX_CONFIG_VERSION,
        "form_weight": d("0.300000"),
        "schedule_weight": d("0.250000"),
        "injury_weight": d("0.300000"),
        "freshness_weight": d("0.100000"),
        "conflict_weight": d("0.050000"),
        "watch_priority_threshold": d("0.350000"),
        "block_priority_threshold": d("0.650000"),
        "schedule_stress_watch": d("0.550000"),
        "schedule_stress_block": d("0.800000"),
        "injury_impact_watch": d("0.300000"),
        "injury_impact_block": d("0.600000"),
        "conflict_watch": d("0.250000"),
        "conflict_block": d("0.500000"),
        "fresh_information_max_age_seconds": d("7200.000000"),
        "stale_information_block_age_seconds": d("43200.000000"),
    }
    values.update(overrides)
    return ResearchSportsMatchSignalMatrixConfig(**values)


def observation(
    match_key: str = "match-alpha-home",
    *,
    league: str = "basketball-pro",
    team_label: str = "Alpha",
    opponent_label: str = "Beta",
    team_side: str = "home",
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    team_form_score: Decimal = d("0.850000"),
    schedule_stress_score: Decimal = d("0.200000"),
    injury_impact_score: Decimal = d("0.100000"),
    signal_conflict_ratio: Decimal = d("0.000000"),
    supporting_signal_count: Decimal = d("4.000000"),
    reason_codes: tuple[str, ...] = ("sports_match_signal_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchSportsMatchSignalMatrixObservation:
    return ResearchSportsMatchSignalMatrixObservation(
        match_key=match_key,
        league=league,
        team_label=team_label,
        opponent_label=opponent_label,
        team_side=team_side,
        observed_at=observed_at,
        team_form_score=team_form_score,
        schedule_stress_score=schedule_stress_score,
        injury_impact_score=injury_impact_score,
        signal_conflict_ratio=signal_conflict_ratio,
        supporting_signal_count=supporting_signal_count,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchSportsMatchSignalMatrixObservation,
    cfg: ResearchSportsMatchSignalMatrixConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchSportsMatchSignalMatrixReport:
    return build_research_sports_match_signal_matrix_report(
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
            schedule_stress_score=d("0.620000"),
            injury_impact_score=d("0.250000"),
        ),
        observation(
            "block-neutral",
            team_label="Charlie",
            team_side="neutral",
            team_form_score=d("0.150000"),
            schedule_stress_score=d("0.900000"),
            injury_impact_score=d("0.700000"),
            signal_conflict_ratio=d("0.650000"),
        ),
    )
    payload = research_sports_match_signal_matrix_payload(matrix_report)

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
    assert set(payload["status"] for payload in payload["rows"]) == {
        "pass",
        "watch",
        "block",
    }
    assert "blocked" not in json.dumps(payload, sort_keys=True)


def test_clear_report_payload_is_decimal_stringed_and_no_advice_surface() -> None:
    matrix_report = report(observation("match-clear"))
    payload = research_sports_match_signal_matrix_payload(matrix_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert matrix_report.status == "pass"
    assert matrix_report.reason_codes == ("sports_match_signal_matrix_pass",)
    assert matrix_report.average_research_priority_score == d("0.118000")
    assert matrix_report.max_research_priority_score == d("0.118000")
    assert matrix_report.average_information_age_seconds == d("3600.000000")
    assert matrix_report.digest.startswith("sports-match-signal-matrix-v0:")

    row = matrix_report.rows[0]
    assert type(row) is ResearchSportsMatchSignalMatrixRow
    assert row.match_key == "match-clear"
    assert row.status == "pass"
    assert row.public_status == "pass"
    assert row.information_age_seconds == d("3600.000000")
    assert row.freshness_score == d("1.000000")
    assert row.research_priority_score == d("0.118000")
    assert row.hard_flag is False
    assert row.reason_codes == (
        "fresh_information",
        "injury_signal_clear",
        "schedule_signal_clear",
        "sports_match_signal_input_available",
        "sports_match_signal_matrix_pass",
    )

    assert payload["subject_count"] == "1.000000"
    assert payload["rows"][0]["research_priority_score"] == "0.118000"
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
        "token",
        "wallet",
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
    ):
        assert unsafe_text not in encoded.lower()


def test_empty_inputs_block_without_rows_and_with_digest() -> None:
    matrix_report = report()

    assert matrix_report.status == "block"
    assert matrix_report.subject_count == ZERO
    assert matrix_report.pass_count == ZERO
    assert matrix_report.watch_count == ZERO
    assert matrix_report.block_count == ZERO
    assert matrix_report.reason_codes == ("sports_match_signal_matrix_no_inputs",)
    assert matrix_report.reason_code_counts == (
        ResearchSportsMatchSignalMatrixReasonCodeCount(
            reason_code="sports_match_signal_matrix_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert matrix_report.rows == ()
    assert matrix_report.digest.startswith("sports-match-signal-matrix-v0:")


def test_decimal_type_rejection_and_datetime_normalization() -> None:
    shifted = report(
        observation(
            observed_at=datetime(
                2026,
                7,
                8,
                8,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
    )
    assert shifted.rows[0].observed_at == GENERATED_AT
    assert shifted.rows[0].information_age_seconds == ZERO

    with pytest.raises(ValueError, match="team_form_score"):
        observation(team_form_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="schedule_stress_score"):
        observation(schedule_stress_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="injury_impact_score"):
        observation(injury_impact_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 15, 30, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 15, 30))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 15, 30, tzinfo=_NoneOffsetTimezone()))


def test_public_leak_rejection_and_hard_flags() -> None:
    matrix_report = report(observation("hard-flags"))

    assert is_dataclass(ResearchSportsMatchSignalMatrixConfig)
    assert is_dataclass(ResearchSportsMatchSignalMatrixObservation)
    assert is_dataclass(ResearchSportsMatchSignalMatrixRow)
    assert is_dataclass(ResearchSportsMatchSignalMatrixReasonCodeCount)
    assert is_dataclass(ResearchSportsMatchSignalMatrixReport)
    with pytest.raises(FrozenInstanceError):
        matrix_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        matrix_report.rows[0].research_priority_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(matrix_report, readonly=False)

    for kwargs in (
        {"match_key": "raw_candidate_123"},
        {"match_key": "market_slug-finals"},
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
            schedule_stress_score=d("0.400000"),
            injury_impact_score=d("0.650000"),
        ),
        observation(
            "stale-watch",
            team_form_score=d("0.700000"),
            schedule_stress_score=d("0.300000"),
            injury_impact_score=d("0.200000"),
            observed_at=GENERATED_AT - timedelta(hours=4),
        ),
    )

    assert matrix_report.status == "block"
    assert matrix_report.hard_flag_count == d("1.000000")
    assert matrix_report.stale_information_count == d("1.000000")
    assert matrix_report.injury_concern_count == d("1.000000")
    assert matrix_report.schedule_congestion_count == d("0.000000")
    assert matrix_report.rows[0].match_key == "injury-block"
    assert matrix_report.rows[0].public_status == "block"
    assert matrix_report.rows[0].hard_flag is True
    assert "injury_signal_block" in matrix_report.rows[0].reason_codes
    assert matrix_report.rows[1].public_status == "watch"
    assert "information_age_watch" in matrix_report.rows[1].reason_codes
    assert (
        ResearchSportsMatchSignalMatrixReasonCodeCount(
            reason_code="sports_match_signal_input_available",
            count=d("2.000000"),
        )
        in matrix_report.reason_code_counts
    )


def test_deterministic_payload_and_report_digest_consistency() -> None:
    first = report(
        observation(
            "z-watch",
            team_label="Zulu",
            schedule_stress_score=d("0.600000"),
            injury_impact_score=d("0.200000"),
        ),
        observation(
            "a-block",
            team_label="Alpha",
            team_form_score=d("0.100000"),
            schedule_stress_score=d("0.900000"),
            injury_impact_score=d("0.800000"),
        ),
        observation("m-pass", team_label="Mike"),
    )
    second = report(
        observation("m-pass", team_label="Mike"),
        observation(
            "a-block",
            team_label="Alpha",
            team_form_score=d("0.100000"),
            schedule_stress_score=d("0.900000"),
            injury_impact_score=d("0.800000"),
        ),
        observation(
            "z-watch",
            team_label="Zulu",
            schedule_stress_score=d("0.600000"),
            injury_impact_score=d("0.200000"),
        ),
    )

    assert first.rows == second.rows
    assert first.digest == second.digest
    assert research_sports_match_signal_matrix_payload(first) == (
        research_sports_match_signal_matrix_payload(second)
    )

    object.__setattr__(first.rows[0], "research_priority_score", d("0.000000"))
    with pytest.raises(ValueError, match="digest|research_priority_score"):
        research_sports_match_signal_matrix_payload(first)


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

    with pytest.raises(ValueError, match="ResearchSportsMatchSignalMatrixReport"):
        research_sports_match_signal_matrix_payload(
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
            if field.name in {"paper_only", "report_only", "readonly"}:
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
