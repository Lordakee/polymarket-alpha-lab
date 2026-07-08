from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_event_volatility_regime_classifier import (
    DEFAULT_RESEARCH_EVENT_VOLATILITY_REGIME_CLASSIFIER_CONFIG_VERSION,
    ResearchEventVolatilityRegimeClassifierConfig,
    ResearchEventVolatilityRegimeClassifierObservation,
    ResearchEventVolatilityRegimeClassifierReasonCodeCount,
    ResearchEventVolatilityRegimeClassifierReport,
    ResearchEventVolatilityRegimeClassifierRow,
    build_research_event_volatility_regime_classifier_report,
    research_event_volatility_regime_classifier_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 16, 0, tzinfo=UTC)
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


def config(**overrides: object) -> ResearchEventVolatilityRegimeClassifierConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_EVENT_VOLATILITY_REGIME_CLASSIFIER_CONFIG_VERSION,
        "event_information_weight": d("0.350000"),
        "liquidity_weight": d("0.250000"),
        "time_window_weight": d("0.200000"),
        "historical_volatility_weight": d("0.200000"),
        "watch_pressure_threshold": d("0.350000"),
        "block_pressure_threshold": d("0.650000"),
        "event_information_watch": d("0.550000"),
        "event_information_block": d("0.850000"),
        "liquidity_watch": d("0.550000"),
        "liquidity_block": d("0.850000"),
        "time_window_watch": d("0.600000"),
        "time_window_block": d("0.900000"),
        "historical_volatility_watch": d("0.500000"),
        "historical_volatility_block": d("0.800000"),
        "fresh_information_max_age_seconds": d("7200.000000"),
        "stale_information_block_age_seconds": d("43200.000000"),
        "watch_confidence_cap": d("0.750000"),
        "block_confidence_cap": d("0.450000"),
    }
    values.update(overrides)
    return ResearchEventVolatilityRegimeClassifierConfig(**values)


def observation(
    event_reference: str = (
        "raw_candidate=alpha-1 market_id=42 market_slug=alpha question=who wins "
        "source_url=https://example.test/source?token=secret dsn=local table=events"
    ),
    *,
    event_family: str = "macro",
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    event_information_shock_score: Decimal = d("0.100000"),
    liquidity_stress_score: Decimal = d("0.100000"),
    time_window_urgency_score: Decimal = d("0.100000"),
    historical_volatility_score: Decimal = d("0.100000"),
    base_confidence: Decimal = d("0.800000"),
    reason_codes: tuple[str, ...] = ("event_volatility_input_available",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventVolatilityRegimeClassifierObservation:
    return ResearchEventVolatilityRegimeClassifierObservation(
        event_reference=event_reference,
        event_family=event_family,
        observed_at=observed_at,
        event_information_shock_score=event_information_shock_score,
        liquidity_stress_score=liquidity_stress_score,
        time_window_urgency_score=time_window_urgency_score,
        historical_volatility_score=historical_volatility_score,
        base_confidence=base_confidence,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: ResearchEventVolatilityRegimeClassifierObservation,
    cfg: ResearchEventVolatilityRegimeClassifierConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventVolatilityRegimeClassifierReport:
    return build_research_event_volatility_regime_classifier_report(
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
    volatility_report = report(
        observation("private-pass", event_family="macro"),
        observation(
            "private-watch",
            event_family="weather",
            event_information_shock_score=d("0.600000"),
            liquidity_stress_score=d("0.200000"),
            time_window_urgency_score=d("0.300000"),
            historical_volatility_score=d("0.300000"),
        ),
        observation(
            "private-block",
            event_family="policy",
            event_information_shock_score=d("0.860000"),
            liquidity_stress_score=d("0.700000"),
            time_window_urgency_score=d("0.500000"),
            historical_volatility_score=d("0.650000"),
        ),
    )
    payload = research_event_volatility_regime_classifier_payload(volatility_report)

    assert volatility_report.status == "block"
    assert volatility_report.subject_count == d("3.000000")
    assert volatility_report.pass_count == d("1.000000")
    assert volatility_report.watch_count == d("1.000000")
    assert volatility_report.block_count == d("1.000000")
    assert volatility_report.hard_flag_count == d("1.000000")
    assert tuple(row.public_status for row in volatility_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert set(row_payload["public_status"] for row_payload in payload["rows"]) == {
        "pass",
        "watch",
        "block",
    }
    assert "blocked" not in json.dumps(payload, sort_keys=True)


def test_clear_report_payload_is_decimal_stringed_and_has_no_trading_advice_surface() -> None:
    volatility_report = report(observation("private-clear"))
    payload = research_event_volatility_regime_classifier_payload(volatility_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert volatility_report.status == "pass"
    assert volatility_report.reason_codes == ("event_volatility_regime_classifier_pass",)
    assert volatility_report.average_volatility_pressure_score == d("0.100000")
    assert volatility_report.max_volatility_pressure_score == d("0.100000")
    assert volatility_report.average_information_age_seconds == d("3600.000000")
    assert volatility_report.digest.startswith("event-volatility-regime-classifier-v0:")

    row = volatility_report.rows[0]
    assert type(row) is ResearchEventVolatilityRegimeClassifierRow
    assert row.event_family == "macro"
    assert row.status == "pass"
    assert row.public_status == "pass"
    assert row.human_review_state == "pass"
    assert row.volatility_regime == "baseline"
    assert row.information_age_seconds == d("3600.000000")
    assert row.freshness_score == d("1.000000")
    assert row.volatility_pressure_score == d("0.100000")
    assert row.confidence_cap == d("1.000000")
    assert row.capped_confidence == d("0.800000")
    assert row.hard_flag is False
    assert row.reason_codes == (
        "event_information_shock_clear",
        "event_volatility_input_available",
        "event_volatility_regime_classifier_pass",
        "fresh_information",
        "historical_volatility_clear",
        "liquidity_stress_clear",
        "time_window_clear",
    )

    assert payload["subject_count"] == "1.000000"
    assert payload["rows"][0]["volatility_pressure_score"] == "0.100000"
    assert payload["digest"] == volatility_report.digest
    assert payload["rows"][0]["digest"] == row.digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) is float for value in walk_payload_values(payload))
    for unsafe_text in (
        "raw_candidate",
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
        "order",
        "trade",
        "position",
        "buy",
        "sell",
        "recommendation",
        "private-clear",
    ):
        assert unsafe_text not in encoded.lower()


def test_empty_inputs_block_without_rows_and_with_digest() -> None:
    volatility_report = report()

    assert volatility_report.status == "block"
    assert volatility_report.subject_count == ZERO
    assert volatility_report.pass_count == ZERO
    assert volatility_report.watch_count == ZERO
    assert volatility_report.block_count == ZERO
    assert volatility_report.reason_codes == ("event_volatility_regime_classifier_no_inputs",)
    assert volatility_report.reason_code_counts == (
        ResearchEventVolatilityRegimeClassifierReasonCodeCount(
            reason_code="event_volatility_regime_classifier_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert volatility_report.rows == ()
    assert volatility_report.digest.startswith("event-volatility-regime-classifier-v0:")


def test_decimal_type_rejection_and_datetime_normalization() -> None:
    shifted = report(
        observation(
            observed_at=datetime(
                2026,
                7,
                8,
                9,
                0,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
    )
    assert shifted.rows[0].observed_at == GENERATED_AT
    assert shifted.rows[0].information_age_seconds == ZERO

    with pytest.raises(ValueError, match="event_information_shock_score"):
        observation(event_information_shock_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="liquidity_stress_score"):
        observation(liquidity_stress_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="historical_volatility_score"):
        observation(historical_volatility_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(observation(), generated_at=_DatetimeSubclass(2026, 7, 8, 16, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 16, 0))
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 8, 16, 0, tzinfo=_NoneOffsetTimezone()))


def test_public_leak_rejection_and_hard_flags() -> None:
    volatility_report = report(observation("hard-flags"))

    assert is_dataclass(ResearchEventVolatilityRegimeClassifierConfig)
    assert is_dataclass(ResearchEventVolatilityRegimeClassifierObservation)
    assert is_dataclass(ResearchEventVolatilityRegimeClassifierRow)
    assert is_dataclass(ResearchEventVolatilityRegimeClassifierReasonCodeCount)
    assert is_dataclass(ResearchEventVolatilityRegimeClassifierReport)
    with pytest.raises(FrozenInstanceError):
        volatility_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        volatility_report.rows[0].volatility_pressure_score = d("0.000000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(volatility_report, readonly=False)

    for kwargs in (
        {"event_family": "market_slug finals"},
        {"event_family": "question desk"},
        {"reason_codes": ("source_url_seen",)},
        {"reason_codes": ("wallet_order_flow",)},
        {"reason_codes": ("buy_signal",)},
    ):
        with pytest.raises(ValueError, match="unsafe|sensitive"):
            observation(**kwargs)


def test_hard_flags_drive_block_status_and_reason_counts() -> None:
    volatility_report = report(
        observation(
            "time-block",
            event_family="weather",
            time_window_urgency_score=d("0.920000"),
            historical_volatility_score=d("0.450000"),
        ),
        observation(
            "historical-watch",
            event_family="macro",
            historical_volatility_score=d("0.550000"),
            observed_at=GENERATED_AT - timedelta(hours=4),
        ),
    )

    assert volatility_report.status == "block"
    assert volatility_report.hard_flag_count == d("1.000000")
    assert volatility_report.stale_information_count == d("1.000000")
    assert volatility_report.urgent_window_count == d("1.000000")
    assert volatility_report.historical_volatility_count == d("2.000000")
    assert volatility_report.rows[0].public_status == "block"
    assert volatility_report.rows[0].human_review_state == "block"
    assert volatility_report.rows[0].hard_flag is True
    assert "time_window_block" in volatility_report.rows[0].reason_codes
    assert volatility_report.rows[1].public_status == "watch"
    assert volatility_report.rows[1].human_review_state == "watch"
    assert "information_age_watch" in volatility_report.rows[1].reason_codes
    assert (
        ResearchEventVolatilityRegimeClassifierReasonCodeCount(
            reason_code="event_volatility_input_available",
            count=d("2.000000"),
        )
        in volatility_report.reason_code_counts
    )


def test_deterministic_payload_and_report_digest_consistency() -> None:
    first = report(
        observation(
            "z-watch",
            event_family="weather",
            event_information_shock_score=d("0.600000"),
            liquidity_stress_score=d("0.200000"),
        ),
        observation(
            "a-block",
            event_family="policy",
            event_information_shock_score=d("0.900000"),
            liquidity_stress_score=d("0.850000"),
        ),
        observation("m-pass", event_family="macro"),
    )
    second = report(
        observation("m-pass", event_family="macro"),
        observation(
            "a-block",
            event_family="policy",
            event_information_shock_score=d("0.900000"),
            liquidity_stress_score=d("0.850000"),
        ),
        observation(
            "z-watch",
            event_family="weather",
            event_information_shock_score=d("0.600000"),
            liquidity_stress_score=d("0.200000"),
        ),
    )

    assert first.rows == second.rows
    assert first.digest == second.digest
    assert research_event_volatility_regime_classifier_payload(first) == (
        research_event_volatility_regime_classifier_payload(second)
    )

    object.__setattr__(first.rows[0], "volatility_pressure_score", d("0.000000"))
    with pytest.raises(ValueError, match="digest|volatility_pressure_score"):
        research_event_volatility_regime_classifier_payload(first)


def test_report_rejects_inconsistent_public_counts_and_unsupported_statuses() -> None:
    volatility_report = report(observation("consistent"))

    with pytest.raises(ValueError, match="subject_count"):
        replace(volatility_report, subject_count=d("2.000000"))
    with pytest.raises(ValueError, match="status"):
        replace(volatility_report, status="blocked")
    with pytest.raises(ValueError, match="average_volatility_pressure_score"):
        replace(volatility_report, average_volatility_pressure_score=d("9.000000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(volatility_report, reason_code_counts=())

    with pytest.raises(ValueError, match="ResearchEventVolatilityRegimeClassifierReport"):
        research_event_volatility_regime_classifier_payload(
            {"paper_only": True, "report_only": True, "readonly": True},
        )  # type: ignore[arg-type]


def test_public_dataclasses_reject_subclassing_and_numeric_public_fields_are_decimal() -> None:
    volatility_report = report(observation("exact"))
    public_values = (
        config(),
        observation("exact-input"),
        volatility_report.rows[0],
        volatility_report.reason_code_counts[0],
        volatility_report,
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
