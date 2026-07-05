from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.market_research_jobless_claims_trend_digest as digest_module
from polymarket_alpha_lab.market_research_jobless_claims_trend_digest import (
    DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION,
    MarketResearchJoblessClaimsTrendDigestConfig,
    MarketResearchJoblessClaimsTrendDigestReasonCodeCount,
    MarketResearchJoblessClaimsTrendDigestReport,
    MarketResearchJoblessClaimsTrendDigestRow,
    MarketResearchJoblessClaimsTrendDigestSignal,
    build_market_research_jobless_claims_trend_digest,
    market_research_jobless_claims_trend_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTZ(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchJoblessClaimsTrendDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION
        ),
        "max_release_age_seconds": d("7200.000000"),
        "min_claims_change": d("5000.000000"),
        "min_claims_change_ratio": d("0.020000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchJoblessClaimsTrendDigestConfig(**values)


def trend_signal(
    condition_id: str = "condition.claims.trend.ready",
    *,
    claims_market_key: str = "us.jobless-claims.trend.ready",
    release_key: str = "dol.jobless-claims.weekly",
    public_signal_reference: str = "dol-jobless-claims-public-release",
    released_at: datetime | None = None,
    prior_claims: Decimal = d("225000.000000"),
    current_claims: Decimal = d("236000.000000"),
    claims_change: Decimal = d("11000.000000"),
    claims_change_ratio: Decimal = d("0.048889"),
    four_week_average_claims: Decimal = d("231000.000000"),
    source_family_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "jobless-claims-trend-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchJoblessClaimsTrendDigestSignal:
    return MarketResearchJoblessClaimsTrendDigestSignal(
        condition_id=condition_id,
        claims_market_key=claims_market_key,
        release_key=release_key,
        public_signal_reference=public_signal_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=30),
        prior_claims=prior_claims,
        current_claims=current_claims,
        claims_change=claims_change,
        claims_change_ratio=claims_change_ratio,
        four_week_average_claims=four_week_average_claims,
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
    cfg: MarketResearchJoblessClaimsTrendDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchJoblessClaimsTrendDigestReport:
    return build_market_research_jobless_claims_trend_digest(
        signals,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_jobless_claims_trend_digest_reduces_redacts_and_sorts() -> None:
    summary = report(
        (
            trend_signal(
                "condition.claims.stale-soft",
                claims_market_key="us.jobless-claims.trend.stale-soft",
                release_key="dol.claims.trend.stale-soft",
                public_signal_reference="https://labor.example/claims?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=4),
                prior_claims=d("230000.000000"),
                current_claims=d("233000.000000"),
                claims_change=d("3000.000000"),
                claims_change_ratio=d("0.013043"),
                four_week_average_claims=d("231500.000000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.450000"),
                base_confidence=d("0.900000"),
            ),
            trend_signal(
                "condition.claims.confirmation-gap",
                claims_market_key="us.jobless-claims.trend.confirmation-gap",
                release_key="dol.claims.trend.confirmation-gap",
                public_signal_reference="wallet://private/claims-trend-note",
                prior_claims=d("220000.000000"),
                current_claims=d("236000.000000"),
                claims_change=d("16000.000000"),
                claims_change_ratio=d("0.072727"),
                four_week_average_claims=d("226000.000000"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                confirmation_ratio=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
            trend_signal(
                "condition.claims.ready",
                claims_market_key="us.jobless-claims.trend.ready",
                release_key="dol.claims.trend.ready",
                public_signal_reference="dol-jobless-claims-public-release",
                prior_claims=d("225000.000000"),
                current_claims=d("238000.000000"),
                claims_change=d("13000.000000"),
                claims_change_ratio=d("0.057778"),
                four_week_average_claims=d("232000.000000"),
                source_family_count=d("4.000000"),
                stale_source_ratio=d("0.050000"),
                confirmation_ratio=d("0.830000"),
                base_confidence=d("0.880000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchJoblessClaimsTrendDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_jobless_claims_trend_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_release_signal_count == d("1.000000")
    assert summary.low_claims_change_signal_count == d("1.000000")
    assert summary.low_claims_change_ratio_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.confirmation_gap_signal_count == d("2.000000")
    assert summary.average_final_confidence == d("0.680000")
    assert summary.average_claims_change == d("10666.666667")
    assert summary.average_claims_change_ratio == d("0.047849")
    assert summary.average_confirmation_ratio == d("0.610000")
    assert summary.max_release_age_seconds == d("14400.000000")
    assert tuple(row.claims_market_key for row in summary.rows) == (
        "us.jobless-claims.trend.stale-soft",
        "us.jobless-claims.trend.confirmation-gap",
        "us.jobless-claims.trend.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.release_age_seconds == d("14400.000000")
    assert blocked.final_confidence == d("0.500000")
    assert blocked.redacted_public_signal_reference == "sha256:0cbc0bb3f2b4"
    assert blocked.reason_codes == (
        "market_research_jobless_claims_trend_digest_stale_release",
        "market_research_jobless_claims_trend_digest_low_claims_change",
        "market_research_jobless_claims_trend_digest_low_claims_change_ratio",
        "market_research_jobless_claims_trend_digest_source_family_gap",
        "market_research_jobless_claims_trend_digest_stale_source_ratio",
        "market_research_jobless_claims_trend_digest_confirmation_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.final_confidence == d("0.660000")
    assert watch.redacted_public_signal_reference == "sha256:3e67af3fb737"
    assert watch.reason_codes == (
        "market_research_jobless_claims_trend_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.880000")
    assert ready.redacted_public_signal_reference == "dol-jobless-claims-public-release"
    assert ready.reason_codes == (
        "market_research_jobless_claims_trend_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code="market_research_jobless_claims_trend_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code="market_research_jobless_claims_trend_digest_stale_release",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code="market_research_jobless_claims_trend_digest_low_claims_change",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code=(
                "market_research_jobless_claims_trend_digest_low_claims_change_ratio"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code="market_research_jobless_claims_trend_digest_source_family_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code="market_research_jobless_claims_trend_digest_stale_source_ratio",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code="market_research_jobless_claims_trend_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )


def test_empty_jobless_claims_trend_digest_blocks_as_missing_evidence() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_jobless_claims_trend_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.average_final_confidence is None
    assert summary.average_claims_change is None
    assert summary.average_claims_change_ratio is None
    assert summary.average_confirmation_ratio is None
    assert summary.max_release_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code="market_research_jobless_claims_trend_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_jobless_claims_trend_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_jobless_claims_trend_digest_payload_is_stable_json_ready_and_decimal_only() -> None:
    summary = report((trend_signal(),))
    payload = market_research_jobless_claims_trend_digest_payload(summary)

    decimal_field_names = {
        "signal_count",
        "ready_signal_count",
        "watch_signal_count",
        "blocked_signal_count",
        "stale_release_signal_count",
        "low_claims_change_signal_count",
        "low_claims_change_ratio_signal_count",
        "source_family_gap_signal_count",
        "stale_source_signal_count",
        "confirmation_gap_signal_count",
        "average_final_confidence",
        "average_claims_change",
        "average_claims_change_ratio",
        "average_confirmation_ratio",
        "max_release_age_seconds",
    }
    for field_name in decimal_field_names:
        assert isinstance(getattr(summary, field_name), Decimal)
        assert payload[field_name] == f"{getattr(summary, field_name):.6f}"
        assert type(payload[field_name]) is str
    assert payload["generated_at"] == "2026-07-03T16:00:00+00:00"

    row_decimal_field_names = {
        "release_age_seconds",
        "prior_claims",
        "current_claims",
        "claims_change",
        "claims_change_ratio",
        "four_week_average_claims",
        "source_family_count",
        "stale_source_ratio",
        "confirmation_ratio",
        "base_confidence",
        "final_confidence",
    }
    assert type(payload["rows"]) is list
    for row, payload_row in zip(summary.rows, payload["rows"], strict=True):
        assert payload_row["released_at"] == row.released_at.isoformat()
        for field_name in row_decimal_field_names:
            assert isinstance(getattr(row, field_name), Decimal)
            assert payload_row[field_name] == f"{getattr(row, field_name):.6f}"
            assert type(payload_row[field_name]) is str

    assert type(payload["reason_code_counts"]) is list
    for item, payload_item in zip(
        summary.reason_code_counts,
        payload["reason_code_counts"],
        strict=True,
    ):
        assert isinstance(item.count, Decimal)
        assert isinstance(item.signal_ratio, Decimal)
        assert payload_item["count"] == f"{item.count:.6f}"
        assert payload_item["signal_ratio"] == f"{item.signal_ratio:.6f}"
        assert type(payload_item["count"]) is str
        assert type(payload_item["signal_ratio"]) is str


def test_jobless_claims_trend_digest_public_numerics_are_exact_six_decimal_decimals() -> None:
    summary = report((trend_signal(),))

    for public_record in (
        config(),
        trend_signal(),
        summary.rows[0],
        summary.reason_code_counts[0],
        summary,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal, field.name
                assert value.as_tuple().exponent == -6, field.name


def test_jobless_claims_trend_digest_payload_revalidates_nested_public_records() -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        summary = report((trend_signal(f"condition.claims.report.{field_name}"),))
        object.__setattr__(summary, field_name, False)
        with pytest.raises(ValueError, match=f"report {field_name} must be True"):
            market_research_jobless_claims_trend_digest_payload(summary)

    for field_name in ("paper_only", "report_only", "readonly"):
        summary = report((trend_signal(f"condition.claims.row.{field_name}"),))
        object.__setattr__(summary.rows[0], field_name, False)
        with pytest.raises(ValueError, match=f"row {field_name} must be True"):
            market_research_jobless_claims_trend_digest_payload(summary)

    for field_name in ("paper_only", "report_only", "readonly"):
        summary = report((trend_signal(f"condition.claims.count.{field_name}"),))
        object.__setattr__(summary.reason_code_counts[0], field_name, False)
        with pytest.raises(ValueError, match=f"reason count {field_name} must be True"):
            market_research_jobless_claims_trend_digest_payload(summary)

    summary = report((trend_signal("condition.claims.non.six.decimal"),))
    object.__setattr__(summary.rows[0], "claims_change_ratio", d("0.0577780"))
    with pytest.raises(ValueError, match="claims_change_ratio must be six-decimal"):
        market_research_jobless_claims_trend_digest_payload(summary)

    summary = report((trend_signal("condition.claims.non.utc.datetime"),))
    object.__setattr__(
        summary.rows[0],
        "released_at",
        (GENERATED_AT - timedelta(minutes=30)).astimezone(timezone(timedelta(hours=-4))),
    )
    with pytest.raises(ValueError, match="released_at must be normalized to UTC"):
        market_research_jobless_claims_trend_digest_payload(summary)

    summary = report((trend_signal("condition.claims.none.offset.datetime"),))
    object.__setattr__(
        summary.rows[0],
        "released_at",
        datetime(2026, 7, 3, 15, 30, tzinfo=_NoneOffsetTZ()),
    )
    with pytest.raises(ValueError, match="released_at must be UTC-aware"):
        market_research_jobless_claims_trend_digest_payload(summary)

    summary = report((trend_signal("condition.claims.bad.nested.row"),))
    object.__setattr__(summary, "rows", (object(),))
    with pytest.raises(ValueError, match="row must be exactly"):
        market_research_jobless_claims_trend_digest_payload(summary)


@pytest.mark.parametrize(
    "value",
    (
        [],
        {},
        set(),
        object(),
    ),
)
def test_jobless_claims_trend_digest_payload_helper_rejects_raw_containers_and_unknown_objects(
    value: object,
) -> None:
    with pytest.raises(ValueError, match="payload contains unsupported value"):
        digest_module._payload_value(value)


def test_jobless_claims_trend_digest_allows_negative_average_claims_change() -> None:
    summary = report(
        (
            trend_signal(
                "condition.claims.decrease",
                claims_market_key="us.jobless-claims.trend.decrease",
                prior_claims=d("236000.000000"),
                current_claims=d("225000.000000"),
                claims_change=d("-11000.000000"),
                claims_change_ratio=d("0.046610"),
            ),
        ),
    )

    assert summary.average_claims_change == d("-11000.000000")
    payload = market_research_jobless_claims_trend_digest_payload(summary)
    assert payload["average_claims_change"] == "-11000.000000"


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_jobless_claims_trend_digest_rejects_false_hard_flags(
    flag_name: str,
) -> None:
    summary = report((trend_signal(),))

    with pytest.raises(ValueError, match=flag_name):
        config(**{flag_name: False})
    with pytest.raises(ValueError, match=flag_name):
        trend_signal(**{flag_name: False})
    with pytest.raises(ValueError, match=flag_name):
        replace(summary.rows[0], **{flag_name: False})
    with pytest.raises(ValueError, match=flag_name):
        replace(summary.reason_code_counts[0], **{flag_name: False})
    with pytest.raises(ValueError, match=flag_name):
        replace(summary, **{flag_name: False})

    unsafe_config = config()
    object.__setattr__(unsafe_config, flag_name, False)
    with pytest.raises(ValueError, match=f"config {flag_name} must be True"):
        report((trend_signal(f"condition.claims.config.{flag_name}"),), cfg=unsafe_config)

    unsafe_signal = trend_signal(f"condition.claims.signal.{flag_name}")
    object.__setattr__(unsafe_signal, flag_name, False)
    with pytest.raises(ValueError, match=f"signal {flag_name} must be True"):
        report((unsafe_signal,))


def test_jobless_claims_trend_digest_dataclasses_are_frozen_and_reject_subclasses() -> None:
    summary = report((trend_signal(),))

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].digest_status = "blocked"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadSignal(MarketResearchJoblessClaimsTrendDigestSignal):
            pass

    with pytest.raises(TypeError):

        class BadConfig(MarketResearchJoblessClaimsTrendDigestConfig):
            pass

    with pytest.raises(TypeError):

        class BadRow(MarketResearchJoblessClaimsTrendDigestRow):
            pass

    with pytest.raises(TypeError):

        class BadReasonCodeCount(MarketResearchJoblessClaimsTrendDigestReasonCodeCount):
            pass

    with pytest.raises(TypeError):

        class BadReport(MarketResearchJoblessClaimsTrendDigestReport):
            pass


def test_jobless_claims_trend_digest_validates_types_utc_and_hard_flags() -> None:
    assert trend_signal(
        released_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    ).released_at == GENERATED_AT

    with pytest.raises(ValueError, match="released_at"):
        trend_signal(released_at=GENERATED_AT.replace(tzinfo=None))
    with pytest.raises(ValueError, match="released_at"):
        trend_signal(released_at=GENERATED_AT.replace(tzinfo=_NoneOffsetTZ()))
    with pytest.raises(ValueError, match="generated_at"):
        report((trend_signal(),), generated_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="claims_change"):
        trend_signal(claims_change=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="condition_id"):
        trend_signal(condition_id=_StringSubclass("condition.claims.bad"))
    with pytest.raises(ValueError, match="readonly"):
        trend_signal(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported")
    with pytest.raises(ValueError, match="signals"):
        report((object(),))


def test_jobless_claims_trend_digest_source_contains_no_durable_or_trading_surface() -> None:
    source_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_jobless_claims_trend_digest.py"
    )
    tree = ast.parse(source_path.read_text())

    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "cancel_order",
        "replace_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import | ast.ImportFrom):
            imported_names = {alias.name for alias in node.names}
            assert not (
                imported_names
                & {"requests", "urllib", "httpx", "socket", "sqlite3", "psycopg"}
            )
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls


def test_jobless_claims_trend_digest_rejects_inconsistent_constructed_report() -> None:
    row = report((trend_signal(),)).rows[0]
    with pytest.raises(ValueError, match="status counts"):
        MarketResearchJoblessClaimsTrendDigestReport(
            generated_at=GENERATED_AT,
            config_version=(
                DEFAULT_MARKET_RESEARCH_JOBLESS_CLAIMS_TREND_DIGEST_CONFIG_VERSION
            ),
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_jobless_claims_trend_digest"
            ),
            signal_count=d("1.000000"),
            ready_signal_count=ZERO,
            watch_signal_count=ZERO,
            blocked_signal_count=ZERO,
            stale_release_signal_count=ZERO,
            low_claims_change_signal_count=ZERO,
            low_claims_change_ratio_signal_count=ZERO,
            source_family_gap_signal_count=ZERO,
            stale_source_signal_count=ZERO,
            confirmation_gap_signal_count=ZERO,
            average_final_confidence=d("0.880000"),
            average_claims_change=d("13000.000000"),
            average_claims_change_ratio=d("0.057778"),
            average_confirmation_ratio=d("0.830000"),
            max_release_age_seconds=d("1800.000000"),
            rows=(row,),
            reason_code_counts=(),
            reason_codes=(),
        )


def test_jobless_claims_trend_digest_rejects_status_counts_that_do_not_match_rows() -> None:
    summary = report((trend_signal(),))

    with pytest.raises(ValueError, match="ready_signal_count"):
        replace(summary, ready_signal_count=ZERO, watch_signal_count=d("1.000000"))


def test_jobless_claims_trend_digest_rejects_reason_counts_that_do_not_match_rows() -> None:
    summary = report((trend_signal(),))

    with pytest.raises(ValueError, match="stale_release_signal_count"):
        replace(summary, stale_release_signal_count=d("1.000000"))


def test_jobless_claims_trend_digest_rejects_aggregates_that_do_not_match_rows() -> None:
    summary = report((trend_signal(),))

    with pytest.raises(ValueError, match="average_final_confidence"):
        replace(summary, average_final_confidence=d("0.000000"))
    with pytest.raises(ValueError, match="max_release_age_seconds"):
        replace(summary, max_release_age_seconds=ZERO)


def test_jobless_claims_trend_digest_rejects_noncanonical_constructed_ordering() -> None:
    summary = report(
        (
            trend_signal("condition.claims.a", claims_market_key="us.jobless-claims.a"),
            trend_signal("condition.claims.b", claims_market_key="us.jobless-claims.b"),
        ),
    )

    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))

    mixed_summary = report(
        (
            trend_signal("condition.claims.ready", claims_market_key="us.jobless-claims.ready"),
            trend_signal(
                "condition.claims.confirmation-gap",
                claims_market_key="us.jobless-claims.confirmation-gap",
                confirmation_ratio=d("0.550000"),
            ),
        ),
    )
    assert len(mixed_summary.reason_code_counts) > 1
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            mixed_summary,
            reason_code_counts=tuple(reversed(mixed_summary.reason_code_counts)),
        )


def test_jobless_claims_trend_digest_rejects_mismatched_reason_count_summary() -> None:
    summary = report((trend_signal(),))

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=())


def test_jobless_claims_trend_digest_rows_use_release_key_tiebreaker() -> None:
    summary = report(
        (
            trend_signal(
                "condition.claims.same",
                claims_market_key="us.jobless-claims.same",
                release_key="dol.claims.week-b",
            ),
            trend_signal(
                "condition.claims.same",
                claims_market_key="us.jobless-claims.same",
                release_key="dol.claims.week-a",
            ),
        ),
    )

    assert tuple(row.release_key for row in summary.rows) == (
        "dol.claims.week-a",
        "dol.claims.week-b",
    )
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))


def test_jobless_claims_trend_digest_rejects_zero_manual_reason_count() -> None:
    with pytest.raises(ValueError, match="count"):
        MarketResearchJoblessClaimsTrendDigestReasonCodeCount(
            reason_code="market_research_jobless_claims_trend_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )


def test_jobless_claims_trend_digest_replace_preserves_validation() -> None:
    summary = report((trend_signal(),))

    replaced = replace(
        summary,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=2))),
    )
    assert replaced.generated_at == GENERATED_AT
    assert replaced.generated_at.tzinfo is UTC

    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(summary, recommended_next_step="trade_market_research_claims")
