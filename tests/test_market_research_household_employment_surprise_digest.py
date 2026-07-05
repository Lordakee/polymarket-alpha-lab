from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_household_employment_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_HOUSEHOLD_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchHouseholdEmploymentSurpriseDigestConfig,
    MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount,
    MarketResearchHouseholdEmploymentSurpriseDigestReport,
    MarketResearchHouseholdEmploymentSurpriseDigestRow,
    MarketResearchHouseholdEmploymentSurpriseDigestSignal,
    build_market_research_household_employment_surprise_digest,
    market_research_household_employment_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchHouseholdEmploymentSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_HOUSEHOLD_EMPLOYMENT_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("10800.000000"),
        "min_household_employment_surprise_score": d("0.600000"),
        "min_unemployment_rate_surprise_score": d("0.500000"),
        "min_participation_rate_surprise_score": d("0.300000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchHouseholdEmploymentSurpriseDigestConfig(**values)


def household_signal(
    condition_id: str = "condition.household.employment",
    *,
    household_employment_key: str = "us.household.employment",
    event_key: str = "bls.household.release",
    household_metric: str = "household_employment",
    public_signal_reference: str = "bls-household-calendar",
    observed_at: datetime | None = None,
    signal_age_seconds: Decimal = d("900.000000"),
    household_employment_surprise_score: Decimal = d("0.720000"),
    unemployment_rate_surprise_score: Decimal = d("0.580000"),
    participation_rate_surprise_score: Decimal = d("0.420000"),
    source_family_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "household-employment-surprise-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchHouseholdEmploymentSurpriseDigestSignal:
    return MarketResearchHouseholdEmploymentSurpriseDigestSignal(
        condition_id=condition_id,
        household_employment_key=household_employment_key,
        event_key=event_key,
        household_metric=household_metric,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        signal_age_seconds=signal_age_seconds,
        household_employment_surprise_score=household_employment_surprise_score,
        unemployment_rate_surprise_score=unemployment_rate_surprise_score,
        participation_rate_surprise_score=participation_rate_surprise_score,
        source_family_count=source_family_count,
        stale_source_ratio=stale_source_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    signals: tuple[object, ...],
    *,
    cfg: MarketResearchHouseholdEmploymentSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchHouseholdEmploymentSurpriseDigestReport:
    return build_market_research_household_employment_surprise_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_household_employment_surprise_digest_reduces_signals_and_sorts() -> None:
    summary = report(
        (
            household_signal(
                "condition.ready",
                household_employment_key="us.household.ready",
                event_key="bls.household.ready",
                public_signal_reference="bls-household-calendar",
                household_employment_surprise_score=d("0.680000"),
                unemployment_rate_surprise_score=d("0.560000"),
                participation_rate_surprise_score=d("0.360000"),
                source_family_count=d("4.000000"),
                stale_source_ratio=d("0.050000"),
                confirmation_ratio=d("0.830000"),
                base_confidence=d("0.880000"),
            ),
            household_signal(
                "condition.soft",
                household_employment_key="us.household.soft",
                event_key="bls.household.soft",
                public_signal_reference="https://labor.example/household?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=4),
                signal_age_seconds=d("14400.000000"),
                household_employment_surprise_score=d("0.300000"),
                unemployment_rate_surprise_score=d("0.200000"),
                participation_rate_surprise_score=d("0.100000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.450000"),
                base_confidence=d("0.900000"),
            ),
            household_signal(
                "condition.watch",
                household_employment_key="us.household.watch",
                event_key="bls.household.watch",
                public_signal_reference="private-household-note",
                household_employment_surprise_score=d("0.700000"),
                unemployment_rate_surprise_score=d("0.640000"),
                participation_rate_surprise_score=d("0.410000"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                confirmation_ratio=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchHouseholdEmploymentSurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_household_employment_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.low_household_employment_surprise_signal_count == d("1.000000")
    assert summary.low_unemployment_rate_surprise_signal_count == d("1.000000")
    assert summary.low_participation_rate_surprise_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.confirmation_gap_signal_count == d("2.000000")
    assert summary.total_confidence_decay == d("0.700000")
    assert summary.average_final_confidence == d("0.613333")
    assert summary.average_household_employment_surprise_score == d("0.560000")
    assert summary.average_unemployment_rate_surprise_score == d("0.466667")
    assert summary.average_participation_rate_surprise_score == d("0.290000")
    assert summary.average_confirmation_ratio == d("0.610000")
    assert summary.max_observed_signal_age_seconds == d("14400.000000")
    assert tuple(row.household_employment_key for row in summary.rows) == (
        "us.household.soft",
        "us.household.watch",
        "us.household.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.observed_signal_age_seconds == d("14400.000000")
    assert blocked.confidence_decay_factor == d("0.600000")
    assert blocked.final_confidence == d("0.300000")
    assert blocked.redacted_public_signal_reference == "sha256:5ea581804642"
    assert blocked.reason_codes == (
        "market_research_household_employment_surprise_digest_stale_signal",
        "market_research_household_employment_surprise_digest_low_household_employment_surprise",
        "market_research_household_employment_surprise_digest_low_unemployment_rate_surprise",
        "market_research_household_employment_surprise_digest_low_participation_rate_surprise",
        "market_research_household_employment_surprise_digest_source_family_gap",
        "market_research_household_employment_surprise_digest_stale_source_ratio",
        "market_research_household_employment_surprise_digest_confirmation_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.confidence_decay_factor == d("0.100000")
    assert watch.final_confidence == d("0.660000")
    assert watch.redacted_public_signal_reference == "sha256:d1e2a0d9c253"
    assert watch.reason_codes == (
        "market_research_household_employment_surprise_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.880000")
    assert ready.redacted_public_signal_reference == "bls-household-calendar"
    assert ready.reason_codes == (
        "market_research_household_employment_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_household_employment_surprise_digest_confirmation_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_household_employment_surprise_digest_stale_signal"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_household_employment_surprise_digest_"
                "low_household_employment_surprise"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_household_employment_surprise_digest_"
                "low_unemployment_rate_surprise"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_household_employment_surprise_digest_"
                "low_participation_rate_surprise"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_household_employment_surprise_digest_"
                "source_family_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_household_employment_surprise_digest_"
                "stale_source_ratio"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code="market_research_household_employment_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )


def test_empty_household_employment_surprise_digest_is_watch_and_decimal_only() -> None:
    summary = report(())

    assert summary.digest_status == "watch"
    assert summary.recommended_next_step == (
        "watch_report_only_market_research_household_employment_surprise_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.average_final_confidence is None
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_household_employment_surprise_digest_no_inputs"
            ),
            count=ZERO,
            signal_ratio=ZERO,
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public_values = asdict(summary)
    numeric_or_countish = (
        "count",
        "ratio",
        "score",
        "confidence",
        "decay",
        "seconds",
    )
    for name, value in public_values.items():
        if any(fragment in name for fragment in numeric_or_countish):
            if isinstance(value, (dict, list, tuple)):
                continue
            assert isinstance(value, Decimal) or value is None, (name, value)


def test_household_employment_surprise_digest_validates_types_flags_and_freezing() -> None:
    signal = household_signal()
    summary = report((signal,))

    with pytest.raises(FrozenInstanceError):
        config().paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal.condition_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].paper_only = False  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadSignal",
            (MarketResearchHouseholdEmploymentSurpriseDigestSignal,),
            {},
        )

    with pytest.raises(ValueError, match="paper_only"):
        replace(signal, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="datetime"):
        report((), generated_at="not-a-datetime")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="datetime"):
        household_signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="Decimal"):
        household_signal(household_employment_surprise_score=_DecimalSubclass("0.7"))
    with pytest.raises(ValueError, match="public string"):
        household_signal(condition_id=_StringSubclass("condition.subclass"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="iterable"):
        build_market_research_household_employment_surprise_digest(
            "not-a-list", config=config(), generated_at=GENERATED_AT,  # type: ignore[arg-type]
        )
    with pytest.raises(
        ValueError,
        match="MarketResearchHouseholdEmploymentSurpriseDigestSignal",
    ):
        report((object(),))


def test_household_employment_surprise_digest_rejects_all_false_phase1_flags() -> None:
    signal = household_signal()
    summary = report((signal,))
    phase1_objects = (
        config(),
        signal,
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    )

    for phase1_object in phase1_objects:
        for flag_name in ("paper_only", "report_only", "readonly"):
            with pytest.raises(ValueError, match=flag_name):
                replace(phase1_object, **{flag_name: False})


def test_household_employment_surprise_digest_payload_is_report_only_and_literal_safe() -> None:
    summary = report((household_signal(),))
    payload = market_research_household_employment_surprise_digest_payload(summary)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["paper_only"] is True
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["rows"][0]["observed_at"] == (
        GENERATED_AT - timedelta(minutes=15)
    ).isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["final_confidence"] == "0.860000"

    src = Path(
        "src/polymarket_alpha_lab/"
        "market_research_household_employment_surprise_digest.py",
    ).read_text(encoding="utf-8")
    tree = ast.parse(src)
    banned_import_prefixes = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "sqlite3",
        "psycopg",
        "supabase",
        "web3",
    )
    banned_call_names = {
        "open",
        "exec",
        "eval",
        "compile",
        "connect",
        "request",
        "post",
        "put",
        "delete",
        "send",
        "submit",
        "cancel",
        "replace",
    }
    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            imported = tuple(alias.name for alias in node.names)
            module = getattr(node, "module", "") or ""
            assert not any(
                name.startswith(banned_import_prefixes) for name in imported
            )
            assert not any(
                module.startswith(name) for name in banned_import_prefixes
            )
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in banned_call_names
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in banned_call_names


def test_household_employment_surprise_digest_payload_rejects_corrupt_phase1_flags() -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        summary = report((household_signal(),))
        object.__setattr__(summary, field_name, False)
        with pytest.raises(ValueError, match=field_name):
            market_research_household_employment_surprise_digest_payload(summary)

    for field_name in ("paper_only", "report_only", "readonly"):
        summary = report((household_signal(),))
        object.__setattr__(summary.rows[0], field_name, False)
        with pytest.raises(ValueError, match=field_name):
            market_research_household_employment_surprise_digest_payload(summary)

    for field_name in ("paper_only", "report_only", "readonly"):
        summary = report((household_signal(),))
        object.__setattr__(summary.reason_code_counts[0], field_name, False)
        with pytest.raises(ValueError, match=field_name):
            market_research_household_employment_surprise_digest_payload(summary)


def test_household_employment_surprise_digest_rows_and_counts_are_frozen_dataclasses() -> None:
    row = MarketResearchHouseholdEmploymentSurpriseDigestRow(
        condition_id="condition.manual",
        household_employment_key="manual.key",
        event_key="manual.event",
        household_metric="manual_metric",
        digest_status="ready",
        observed_at=GENERATED_AT,
        observed_signal_age_seconds=d("0.000000"),
        input_signal_age_seconds=d("0.000000"),
        household_employment_surprise_score=d("0.700000"),
        unemployment_rate_surprise_score=d("0.600000"),
        participation_rate_surprise_score=d("0.400000"),
        source_family_count=d("3.000000"),
        stale_source_ratio=d("0.000000"),
        confirmation_ratio=d("0.900000"),
        base_confidence=d("0.850000"),
        confidence_decay_factor=d("0.000000"),
        final_confidence=d("0.850000"),
        redacted_public_signal_reference="manual-reference",
        reason_codes=(
            "market_research_household_employment_surprise_digest_ready",
        ),
    )
    reason = MarketResearchHouseholdEmploymentSurpriseDigestReasonCodeCount(
        reason_code="market_research_household_employment_surprise_digest_ready",
        count=d("1.000000"),
        signal_ratio=d("1.000000"),
    )

    assert is_dataclass(row)
    assert is_dataclass(reason)
    with pytest.raises(FrozenInstanceError):
        row.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason.count = d("2.000000")  # type: ignore[misc]
