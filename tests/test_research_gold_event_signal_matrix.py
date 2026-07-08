from __future__ import annotations

import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from typing import Any

import pytest

from polymarket_alpha_lab.research_gold_event_signal_matrix import (
    DEFAULT_RESEARCH_GOLD_EVENT_SIGNAL_MATRIX_CONFIG_VERSION,
    GoldEventSignalMatrixCandidate,
    GoldEventSignalMatrixConfig,
    GoldEventSignalMatrixReasonCodeCount,
    GoldEventSignalMatrixReport,
    GoldEventSignalMatrixRow,
    build_research_gold_event_signal_matrix_report,
    research_gold_event_signal_matrix_digest,
    research_gold_event_signal_matrix_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)
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


def config(**overrides: object) -> GoldEventSignalMatrixConfig:
    values = {
        "config_version": DEFAULT_RESEARCH_GOLD_EVENT_SIGNAL_MATRIX_CONFIG_VERSION,
        "dollar_pressure_watch": d("0.500000"),
        "dollar_pressure_block": d("0.800000"),
        "real_rate_pressure_watch": d("0.500000"),
        "real_rate_pressure_block": d("0.800000"),
        "central_bank_signal_watch": d("0.450000"),
        "central_bank_signal_block": d("0.750000"),
        "risk_appetite_shift_watch": d("0.450000"),
        "risk_appetite_shift_block": d("0.750000"),
        "source_confidence_watch": d("0.500000"),
        "source_confidence_block": d("0.250000"),
        "recency_watch_seconds": d("86400.000000"),
        "recency_block_seconds": d("259200.000000"),
    }
    values.update(overrides)
    return GoldEventSignalMatrixConfig(**values)


def candidate(
    public_event_label: str = "gold-dollar-real-rate-window",
    *,
    metal_family: str = "gold",
    event_family: str = "macro-cross-asset",
    dollar_pressure_score: Decimal = d("0.300000"),
    real_rate_pressure_score: Decimal = d("0.300000"),
    central_bank_signal_score: Decimal = d("0.200000"),
    risk_appetite_shift_score: Decimal = d("0.200000"),
    source_confidence_score: Decimal = d("0.900000"),
    recency_seconds: Decimal = d("3600.000000"),
    evidence_family_count: Decimal = d("4.000000"),
    reason_codes: tuple[str, ...] = ("gold_event_signal_input_available",),
    observed_at: datetime = GENERATED_AT - timedelta(hours=1),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> GoldEventSignalMatrixCandidate:
    return GoldEventSignalMatrixCandidate(
        public_event_label=public_event_label,
        metal_family=metal_family,
        event_family=event_family,
        dollar_pressure_score=dollar_pressure_score,
        real_rate_pressure_score=real_rate_pressure_score,
        central_bank_signal_score=central_bank_signal_score,
        risk_appetite_shift_score=risk_appetite_shift_score,
        source_confidence_score=source_confidence_score,
        recency_seconds=recency_seconds,
        evidence_family_count=evidence_family_count,
        reason_codes=reason_codes,
        observed_at=observed_at,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *rows: GoldEventSignalMatrixCandidate,
    cfg: GoldEventSignalMatrixConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> GoldEventSignalMatrixReport:
    return build_research_gold_event_signal_matrix_report(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def assert_no_float(value: Any) -> None:
    if isinstance(value, float):
        pytest.fail(f"found float in public payload: {value!r}")
    if isinstance(value, dict):
        for key, item in value.items():
            assert_no_float(key)
            assert_no_float(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float(item)


def test_pass_watch_block_rows_roll_up_to_public_research_report() -> None:
    matrix_report = report(
        candidate("z-pass", dollar_pressure_score=d("0.200000")),
        candidate(
            "m-watch",
            dollar_pressure_score=d("0.600000"),
            real_rate_pressure_score=d("0.550000"),
            central_bank_signal_score=d("0.500000"),
            risk_appetite_shift_score=d("0.500000"),
        ),
        candidate(
            "a-block",
            dollar_pressure_score=d("0.900000"),
            real_rate_pressure_score=d("0.850000"),
            central_bank_signal_score=d("0.800000"),
            source_confidence_score=d("0.200000"),
        ),
    )

    assert matrix_report.status == "block"
    assert matrix_report.candidate_count == d("3.000000")
    assert matrix_report.pass_count == d("1.000000")
    assert matrix_report.watch_count == d("1.000000")
    assert matrix_report.block_count == d("1.000000")
    assert matrix_report.hard_flag_count == d("1.000000")
    assert tuple(row.public_event_label for row in matrix_report.rows) == (
        "a-block",
        "m-watch",
        "z-pass",
    )
    assert tuple(row.public_status for row in matrix_report.rows) == (
        "block",
        "watch",
        "pass",
    )
    assert matrix_report.reason_codes == (
        "gold_event_signal_matrix_block",
        "central_bank_signal_block",
        "central_bank_signal_watch",
        "dollar_pressure_block",
        "dollar_pressure_watch",
        "real_rate_pressure_block",
        "real_rate_pressure_watch",
        "risk_appetite_shift_watch",
        "source_confidence_block",
    )


def test_decimal_only_and_type_rejection() -> None:
    matrix_report = report(candidate("decimal-only"))

    assert is_dataclass(GoldEventSignalMatrixConfig)
    assert is_dataclass(GoldEventSignalMatrixCandidate)
    assert is_dataclass(GoldEventSignalMatrixRow)
    assert is_dataclass(GoldEventSignalMatrixReasonCodeCount)
    assert is_dataclass(GoldEventSignalMatrixReport)
    with pytest.raises(FrozenInstanceError):
        matrix_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        matrix_report.rows[0].research_priority_score = d("0.900000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="dollar_pressure_score"):
        candidate(dollar_pressure_score=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_confidence_score"):
        candidate(source_confidence_score=_DecimalSubclass("0.900000"))
    with pytest.raises(ValueError, match="candidate_count"):
        replace(matrix_report, candidate_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 8, 13, 0, tzinfo=UTC))

    for item in (matrix_report, *matrix_report.rows, *matrix_report.reason_code_counts):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly", "hard_flag"}:
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_public_leak_rejection_for_identifiers_sources_and_actions() -> None:
    forbidden_values = (
        "candidate_id_123",
        "market-id-123",
        "market_slug_gold",
        "will gold close higher question",
        "source_ref_internal",
        "https://example.test/source",
        "raw source text excerpt",
        "postgres_dsn",
        "table_name",
        "api_token",
        "wallet-alpha",
        "order-field",
        "trade-field",
        "buy-recommendation",
        "sell-signal",
        "position-size",
    )
    for value in forbidden_values:
        with pytest.raises(ValueError, match="unsafe"):
            candidate(public_event_label=value)

    matrix_report = report(candidate("safe-public-label"))
    object.__setattr__(matrix_report.rows[0], "public_event_label", "wallet leak")
    with pytest.raises(ValueError, match="unsafe"):
        research_gold_event_signal_matrix_payload(matrix_report)


def test_hard_flags_are_required_on_every_public_surface() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        candidate(report_only=False)

    matrix_report = report(candidate("flag-row"))
    with pytest.raises(ValueError, match="readonly"):
        replace(matrix_report, readonly=False)
    object.__setattr__(matrix_report.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        research_gold_event_signal_matrix_payload(matrix_report)


def test_deterministic_payload_and_digest_are_stable_and_consistent() -> None:
    inputs = (
        candidate("z-watch", dollar_pressure_score=d("0.600000")),
        candidate("a-pass", dollar_pressure_score=d("0.200000")),
    )
    first = report(*inputs)
    second = report(*reversed(inputs))

    first_payload = research_gold_event_signal_matrix_payload(first)
    second_payload = research_gold_event_signal_matrix_payload(second)
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True) == json.dumps(
        second_payload,
        sort_keys=True,
    )
    assert_no_float(first_payload)

    digest_payload = research_gold_event_signal_matrix_digest(first)
    assert digest_payload == {
        "generated_at": GENERATED_AT.isoformat(),
        "config_version": DEFAULT_RESEARCH_GOLD_EVENT_SIGNAL_MATRIX_CONFIG_VERSION,
        "status": first_payload["status"],
        "candidate_count": first_payload["candidate_count"],
        "pass_count": first_payload["pass_count"],
        "watch_count": first_payload["watch_count"],
        "block_count": first_payload["block_count"],
        "hard_flag_count": first_payload["hard_flag_count"],
        "reason_codes": first_payload["reason_codes"],
        "top_rows": first_payload["rows"][:3],
        "digest": first_payload["digest"],
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }


def test_empty_inputs_block_without_leaking_source_data() -> None:
    matrix_report = report()

    assert matrix_report.status == "block"
    assert matrix_report.candidate_count == ZERO
    assert matrix_report.reason_codes == ("gold_event_signal_matrix_no_inputs",)
    assert matrix_report.reason_code_counts == (
        GoldEventSignalMatrixReasonCodeCount(
            reason_code="gold_event_signal_matrix_no_inputs",
            count=d("1.000000"),
        ),
    )
    assert matrix_report.rows == ()
    assert matrix_report.digest.startswith("gold-event-signal-matrix-v0:")


def test_datetime_normalization_and_public_status_validation() -> None:
    with pytest.raises(ValueError, match="observed_at"):
        candidate(observed_at=datetime(2026, 7, 8, 13, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(candidate("time"), generated_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="observed_at"):
        candidate(
            observed_at=datetime(2026, 7, 8, 13, 0, tzinfo=_NoneOffsetTimezone()),
        )

    shifted = report(
        candidate(
            "offset-time",
            observed_at=datetime(2026, 7, 8, 7, 0, tzinfo=timezone(timedelta(hours=-6))),
        ),
    )
    assert shifted.rows[0].observed_at == datetime(2026, 7, 8, 13, 0, tzinfo=UTC)

    with pytest.raises(ValueError, match="public_status"):
        GoldEventSignalMatrixRow(
            public_event_label="bad-status",
            metal_family="gold",
            event_family="macro-cross-asset",
            public_status="blocked",
            hard_flag=False,
            dollar_pressure_score=d("0.900000"),
            real_rate_pressure_score=d("0.900000"),
            central_bank_signal_score=d("0.100000"),
            risk_appetite_shift_score=d("0.100000"),
            source_confidence_score=d("0.900000"),
            recency_seconds=d("3600.000000"),
            evidence_family_count=d("3.000000"),
            research_priority_score=d("0.900000"),
            observed_at=GENERATED_AT,
            reason_codes=("gold_event_signal_input_available",),
        )
