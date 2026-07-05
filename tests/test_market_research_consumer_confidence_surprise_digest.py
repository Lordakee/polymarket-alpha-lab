from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_consumer_confidence_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_CONSUMER_CONFIDENCE_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchConsumerConfidenceSurpriseDigestConfig,
    MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount,
    MarketResearchConsumerConfidenceSurpriseDigestReport,
    MarketResearchConsumerConfidenceSurpriseDigestRow,
    MarketResearchConsumerConfidenceSurpriseDigestSignal,
    build_market_research_consumer_confidence_surprise_digest,
    market_research_consumer_confidence_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 15, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchConsumerConfidenceSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CONSUMER_CONFIDENCE_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold": d("0.050000"),
        "max_revision_ratio": d("0.200000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchConsumerConfidenceSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_consumer_confidence",
    *,
    research_key: str = "research.consumer_confidence.umich",
    release_key: str = "consumer_confidence.umich.final",
    survey_family: str = "umich",
    public_signal_reference: str = "public-umich-confidence",
    observed_at: datetime | None = None,
    expected_index: Decimal = d("69.000000"),
    actual_index: Decimal = d("67.500000"),
    surprise_score: Decimal = d("0.020000"),
    source_count: Decimal = d("3"),
    revision_ratio: Decimal = d("0.050000"),
    confirmation_ratio: Decimal = d("0.850000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "consumer-confidence-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchConsumerConfidenceSurpriseDigestSignal:
    return MarketResearchConsumerConfidenceSurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        survey_family=survey_family,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        expected_index=expected_index,
        actual_index=actual_index,
        surprise_score=surprise_score,
        source_count=source_count,
        revision_ratio=revision_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchConsumerConfidenceSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchConsumerConfidenceSurpriseDigestReport:
    return build_market_research_consumer_confidence_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_consumer_confidence_surprise_digest_reduces_and_sorts_deterministically() -> None:
    summary = report(
        (
            signal(
                "condition_cb",
                research_key="research.consumer_confidence.conference_board",
                release_key="consumer_confidence.conference_board",
                survey_family="conference_board",
                public_signal_reference="https://vendor.example/confidence?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                expected_index=d("104.000000"),
                actual_index=d("96.000000"),
                surprise_score=d("0.090000"),
                source_count=d("1"),
                revision_ratio=d("0.350000"),
                confirmation_ratio=d("0.420000"),
                base_confidence=d("0.880000"),
            ),
            signal(
                "condition_morning_consult",
                research_key="research.consumer_confidence.morning_consult",
                release_key="consumer_confidence.morning_consult",
                survey_family="morning_consult",
                public_signal_reference="public-morning-consult-confidence",
                observed_at=GENERATED_AT - timedelta(minutes=25),
                expected_index=d("102.000000"),
                actual_index=d("101.400000"),
                surprise_score=d("0.010000"),
                source_count=d("3"),
                revision_ratio=d("0.040000"),
                confirmation_ratio=d("0.900000"),
                base_confidence=d("0.920000"),
            ),
            signal(
                "condition_umich",
                research_key="research.consumer_confidence.umich",
                release_key="consumer_confidence.umich.prelim",
                survey_family="umich",
                public_signal_reference="private-confidence-feed",
                observed_at=GENERATED_AT - timedelta(hours=1),
                expected_index=d("69.000000"),
                actual_index=d("64.500000"),
                surprise_score=d("0.070000"),
                source_count=d("2"),
                revision_ratio=d("0.120000"),
                confirmation_ratio=d("0.600000"),
                base_confidence=d("0.850000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_CONSUMER_CONFIDENCE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_consumer_confidence_surprise_digest"
    )
    assert summary.signal_count == d("3")
    assert summary.ready_signal_count == d("1")
    assert summary.watch_signal_count == d("1")
    assert summary.blocked_signal_count == d("1")
    assert summary.material_surprise_count == d("2")
    assert summary.stale_signal_count == d("1")
    assert summary.thin_source_count == d("1")
    assert summary.high_revision_count == d("1")
    assert summary.confirmation_gap_count == d("2")
    assert summary.average_surprise_score == d("0.056667")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.release_key for row in summary.rows) == (
        "consumer_confidence.conference_board",
        "consumer_confidence.umich.prelim",
        "consumer_confidence.morning_consult",
    )

    conference_board = summary.rows[0]
    assert conference_board.digest_status == "blocked"
    assert conference_board.signal_age_seconds == d("10800.000000")
    assert conference_board.surprise_delta == d("-8.000000")
    assert conference_board.confidence_decay_factor == d("0.400000")
    assert conference_board.final_confidence == d("0.352000")
    assert conference_board.redacted_public_signal_reference == "sha256:3937b38286f0"
    assert conference_board.reason_codes == (
        "market_research_consumer_confidence_surprise_digest_stale_signal",
        "market_research_consumer_confidence_surprise_digest_material_surprise",
        "market_research_consumer_confidence_surprise_digest_thin_sources",
        "market_research_consumer_confidence_surprise_digest_high_revision",
        "market_research_consumer_confidence_surprise_digest_confirmation_gap",
    )

    umich = summary.rows[1]
    assert umich.digest_status == "watch"
    assert umich.signal_age_seconds == d("3600.000000")
    assert umich.surprise_delta == d("-4.500000")
    assert umich.confidence_decay_factor == d("0.800000")
    assert umich.final_confidence == d("0.680000")
    assert umich.redacted_public_signal_reference == "sha256:2eaebc1fb3cb"
    assert umich.reason_codes == (
        "market_research_consumer_confidence_surprise_digest_material_surprise",
        "market_research_consumer_confidence_surprise_digest_confirmation_gap",
    )

    morning_consult = summary.rows[2]
    assert morning_consult.digest_status == "ready"
    assert morning_consult.signal_age_seconds == d("1500.000000")
    assert morning_consult.surprise_delta == d("-0.600000")
    assert morning_consult.confidence_decay_factor == d("1.000000")
    assert morning_consult.final_confidence == d("0.920000")
    assert morning_consult.redacted_public_signal_reference == (
        "public-morning-consult-confidence"
    )
    assert morning_consult.reason_codes == (
        "market_research_consumer_confidence_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_consumer_confidence_surprise_digest_"
                "confirmation_gap"
            ),
            count=d("2"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_consumer_confidence_surprise_digest_"
                "material_surprise"
            ),
            count=d("2"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_confidence_surprise_digest_stale_signal",
            count=d("1"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_confidence_surprise_digest_thin_sources",
            count=d("1"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_confidence_surprise_digest_high_revision",
            count=d("1"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_confidence_surprise_digest_ready",
            count=d("1"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "secret-123",
        "vendor.example",
        "https://",
        "private-confidence-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "order",
    ):
        assert token not in public


def test_consumer_confidence_digest_empty_inputs_are_blocked_with_decimal_counts() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.signal_count == ZERO
    assert summary.rows == ()
    assert summary.average_surprise_score is None
    assert summary.max_signal_age_seconds is None
    assert summary.average_source_count is None
    assert summary.reason_code_counts == (
        MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_confidence_surprise_digest_no_inputs",
            count=d("1"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_consumer_confidence_surprise_digest_no_inputs",
    )


def test_consumer_confidence_digest_dataclasses_are_frozen_and_decimal_only() -> None:
    cfg = config()
    source = signal(observed_at=datetime(2026, 7, 3, 10, 30, tzinfo=timezone.utc))
    summary = report((source,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        source.source_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].final_confidence = d("0.500000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.signal_count = d("2")  # type: ignore[misc]

    assert source.observed_at.tzinfo is UTC
    assert summary.rows[0].observed_at.tzinfo is UTC
    assert summary.generated_at.tzinfo is UTC

    numeric_public_fields = {
        "max_signal_age_seconds",
        "min_source_count",
        "material_surprise_threshold",
        "max_revision_ratio",
        "min_confirmation_ratio",
        "watch_confidence_threshold",
        "expected_index",
        "actual_index",
        "surprise_score",
        "source_count",
        "revision_ratio",
        "confirmation_ratio",
        "base_confidence",
        "signal_age_seconds",
        "surprise_delta",
        "confidence_decay_factor",
        "final_confidence",
        "signal_count",
        "ready_signal_count",
        "watch_signal_count",
        "blocked_signal_count",
        "material_surprise_count",
        "stale_signal_count",
        "thin_source_count",
        "high_revision_count",
        "confirmation_gap_count",
        "average_surprise_score",
        "max_signal_age_seconds",
        "average_source_count",
        "count",
        "signal_ratio",
    }
    for item in (cfg, source, summary, summary.rows[0], summary.reason_code_counts[0]):
        for field_name, value in asdict(item).items():
            if field_name in numeric_public_fields and value is not None:
                assert type(value) is Decimal, (field_name, type(value))
                assert value.as_tuple().exponent == -6


@pytest.mark.parametrize(
    ("factory", "message"),
    (
        (
            lambda: config(paper_only=False),
            "paper_only",
        ),
        (
            lambda: config(report_only=False),
            "report_only",
        ),
        (
            lambda: config(readonly=False),
            "readonly",
        ),
        (
            lambda: config(min_source_count=2),
            "Decimal",
        ),
        (
            lambda: signal(source_count=d("-1")),
            "source_count",
        ),
        (
            lambda: signal(surprise_score=d("1.500000")),
            "surprise_score",
        ),
        (
            lambda: signal(public_signal_reference="wallet source"),
            "public_signal_reference",
        ),
        (
            lambda: signal(signal_config_version=_StringSubclass("config-v0")),
            "signal_config_version",
        ),
        (
            lambda: signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC)),
            "observed_at",
        ),
    ),
)
def test_consumer_confidence_digest_validates_inputs_and_flags(
    factory: object,
    message: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        factory()


def test_consumer_confidence_digest_rejects_subclass_definitions() -> None:
    with pytest.raises(TypeError, match="subclassing"):
        class ConfigSubclass(MarketResearchConsumerConfidenceSurpriseDigestConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class SignalSubclass(MarketResearchConsumerConfidenceSurpriseDigestSignal):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class RowSubclass(MarketResearchConsumerConfidenceSurpriseDigestRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReasonCodeCountSubclass(
            MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReportSubclass(MarketResearchConsumerConfidenceSurpriseDigestReport):
            pass


def test_consumer_confidence_digest_rejects_inconsistent_reports() -> None:
    good = report((signal(),))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(good, reason_codes=("unexpected",))
    with pytest.raises(ValueError, match="signal_count"):
        replace(good, signal_count=d("99"))
    with pytest.raises(ValueError, match="count"):
        MarketResearchConsumerConfidenceSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_confidence_surprise_digest_no_inputs",
            count=ZERO,
            signal_ratio=ZERO,
        )

    ready_row = good.rows[0]
    with pytest.raises(ValueError, match="unique"):
        replace(
            ready_row,
            reason_codes=(
                "market_research_consumer_confidence_surprise_digest_ready",
                "market_research_consumer_confidence_surprise_digest_ready",
            ),
        )
    with pytest.raises(ValueError, match="ready"):
        replace(
            ready_row,
            digest_status="watch",
            reason_codes=(
                "market_research_consumer_confidence_surprise_digest_material_surprise",
                "market_research_consumer_confidence_surprise_digest_ready",
            ),
        )


def test_consumer_confidence_digest_rejects_noncanonical_constructor_order() -> None:
    summary = report(
        (
            signal("condition_b", release_key="release.b", surprise_score=d("0.100000")),
            signal("condition_a", release_key="release.a", surprise_score=d("0.100000")),
        ),
    )
    assert tuple(row.condition_id for row in summary.rows) == (
        "condition_a",
        "condition_b",
    )

    with pytest.raises(ValueError, match="rows.*sorted"):
        replace(summary, rows=tuple(reversed(summary.rows)))

    multi_reason_summary = report(
        (
            signal(
                surprise_score=d("0.070000"),
                confirmation_ratio=d("0.600000"),
            ),
        ),
    )
    multi_reason_row = multi_reason_summary.rows[0]
    assert multi_reason_row.reason_codes == (
        "market_research_consumer_confidence_surprise_digest_material_surprise",
        "market_research_consumer_confidence_surprise_digest_confirmation_gap",
    )
    with pytest.raises(ValueError, match="reason_code_counts.*sorted"):
        replace(
            multi_reason_summary,
            reason_code_counts=tuple(reversed(multi_reason_summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes.*sorted"):
        replace(
            multi_reason_summary,
            reason_codes=tuple(reversed(multi_reason_summary.reason_codes)),
        )
    with pytest.raises(ValueError, match="reason_codes.*sorted"):
        replace(multi_reason_row, reason_codes=tuple(reversed(multi_reason_row.reason_codes)))


def test_consumer_confidence_digest_rejects_none_offset_timezones() -> None:
    none_offset_time = datetime(2026, 7, 3, 12, 0, tzinfo=_NoneOffsetTimezone())

    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=none_offset_time)
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report((signal(),), generated_at=none_offset_time)
    with pytest.raises(ValueError, match="payload datetime must be timezone-aware"):
        market_research_consumer_confidence_surprise_digest_payload(
            {"generated_at": none_offset_time},
        )


def test_consumer_confidence_digest_payload_is_public_and_deterministic() -> None:
    summary = report(
        (
            signal("condition_b", release_key="release.b", surprise_score=d("0.100000")),
            signal("condition_a", release_key="release.a", surprise_score=d("0.100000")),
        ),
    )
    payload = market_research_consumer_confidence_surprise_digest_payload(summary)

    assert payload == market_research_consumer_confidence_surprise_digest_payload(summary)
    assert payload["digest_status"] == summary.digest_status
    assert payload["signal_count"] == "2.000000"
    assert [row["condition_id"] for row in payload["rows"]] == [
        "condition_a",
        "condition_b",
    ]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "persisted" not in payload
    assert "dsn" not in payload
    assert "wallet" not in repr(payload).lower()

    assert market_research_consumer_confidence_surprise_digest_payload(payload) == payload
    raw_payload = market_research_consumer_confidence_surprise_digest_payload(
        {
            "generated_at": GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
            "signal_count": d("2"),
            "rows": (
                {
                    "observed_at": GENERATED_AT,
                    "surprise_score": d("0.1"),
                },
            ),
        },
    )
    assert raw_payload["generated_at"] == "2026-07-03T15:00:00+00:00"
    assert raw_payload["signal_count"] == "2.000000"
    assert raw_payload["rows"] == [
        {
            "observed_at": "2026-07-03T15:00:00+00:00",
            "surprise_score": "0.100000",
        },
    ]
    with pytest.raises(TypeError, match="Decimal"):
        market_research_consumer_confidence_surprise_digest_payload(
            {"signal_count": _DecimalSubclass("2")},
        )
    with pytest.raises(ValueError, match="report"):
        market_research_consumer_confidence_surprise_digest_payload(object())


def test_consumer_confidence_digest_rejects_false_flags_on_public_records() -> None:
    summary = report((signal(),))
    row = summary.rows[0]
    reason_count = summary.reason_code_counts[0]

    for factory in (
        lambda: config(paper_only=False),
        lambda: config(report_only=False),
        lambda: config(readonly=False),
        lambda: signal(paper_only=False),
        lambda: signal(report_only=False),
        lambda: signal(readonly=False),
        lambda: replace(row, paper_only=False),
        lambda: replace(row, report_only=False),
        lambda: replace(row, readonly=False),
        lambda: replace(reason_count, paper_only=False),
        lambda: replace(reason_count, report_only=False),
        lambda: replace(reason_count, readonly=False),
        lambda: replace(summary, paper_only=False),
        lambda: replace(summary, report_only=False),
        lambda: replace(summary, readonly=False),
    ):
        with pytest.raises(ValueError, match="must be True"):
            factory()


def test_consumer_confidence_digest_module_has_no_durable_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_consumer_confidence_surprise_digest.py"
    )
    tree = ast.parse(module_path.read_text())

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            call = node.func
            if isinstance(call, ast.Name):
                assert call.id not in forbidden_call_names
            elif isinstance(call, ast.Attribute):
                assert call.attr not in forbidden_call_names
