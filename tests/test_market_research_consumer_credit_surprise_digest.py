from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_consumer_credit_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_CONSUMER_CREDIT_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchConsumerCreditSurpriseDigestConfig,
    MarketResearchConsumerCreditSurpriseDigestReasonCodeCount,
    MarketResearchConsumerCreditSurpriseDigestReport,
    MarketResearchConsumerCreditSurpriseDigestRow,
    MarketResearchConsumerCreditSurpriseDigestSignal,
    build_market_research_consumer_credit_surprise_digest,
    market_research_consumer_credit_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchConsumerCreditSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CONSUMER_CREDIT_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.030000"),
        "max_revision_ratio": d("0.200000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchConsumerCreditSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_consumer_credit",
    *,
    research_key: str = "research.consumer_credit.revolving",
    release_key: str = "consumer_credit.federal_reserve.g19",
    credit_segment: str = "revolving",
    public_signal_reference: str = "public-consumer-credit-g19",
    observed_at: datetime | None = None,
    expected_credit_change: Decimal = d("12.000000"),
    actual_credit_change: Decimal = d("14.000000"),
    surprise_score: Decimal = d("0.020000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.050000"),
    confirmation_ratio: Decimal = d("0.850000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "consumer-credit-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchConsumerCreditSurpriseDigestSignal:
    return MarketResearchConsumerCreditSurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        credit_segment=credit_segment,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        expected_credit_change=expected_credit_change,
        actual_credit_change=actual_credit_change,
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
    cfg: MarketResearchConsumerCreditSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchConsumerCreditSurpriseDigestReport:
    return build_market_research_consumer_credit_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_consumer_credit_surprise_digest_reduces_and_sorts_deterministically() -> None:
    summary = report(
        (
            signal(
                "condition_revolving",
                research_key="research.consumer_credit.revolving",
                release_key="consumer_credit.g19.revolving",
                credit_segment="revolving",
                public_signal_reference="https://vendor.example/credit?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                expected_credit_change=d("10.000000"),
                actual_credit_change=d("18.000000"),
                surprise_score=d("0.080000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.350000"),
                confirmation_ratio=d("0.420000"),
                base_confidence=d("0.880000"),
            ),
            signal(
                "condition_total",
                research_key="research.consumer_credit.total",
                release_key="consumer_credit.g19.total",
                credit_segment="total",
                public_signal_reference="public-consumer-credit-total",
                observed_at=GENERATED_AT - timedelta(minutes=25),
                expected_credit_change=d("16.000000"),
                actual_credit_change=d("16.500000"),
                surprise_score=d("0.010000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.040000"),
                confirmation_ratio=d("0.900000"),
                base_confidence=d("0.920000"),
            ),
            signal(
                "condition_nonrevolving",
                research_key="research.consumer_credit.nonrevolving",
                release_key="consumer_credit.g19.nonrevolving",
                credit_segment="nonrevolving",
                public_signal_reference="private-credit-feed",
                observed_at=GENERATED_AT - timedelta(hours=1),
                expected_credit_change=d("6.000000"),
                actual_credit_change=d("2.000000"),
                surprise_score=d("0.040000"),
                source_count=d("2.000000"),
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
        DEFAULT_MARKET_RESEARCH_CONSUMER_CREDIT_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_consumer_credit_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.material_surprise_count == d("2.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.high_revision_count == d("1.000000")
    assert summary.confirmation_gap_count == d("2.000000")
    assert summary.average_surprise_score == d("0.043333")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.release_key for row in summary.rows) == (
        "consumer_credit.g19.revolving",
        "consumer_credit.g19.nonrevolving",
        "consumer_credit.g19.total",
    )

    revolving = summary.rows[0]
    assert revolving.digest_status == "blocked"
    assert revolving.signal_age_seconds == d("10800.000000")
    assert revolving.surprise_delta == d("8.000000")
    assert revolving.confidence_decay_factor == d("0.400000")
    assert revolving.final_confidence == d("0.352000")
    assert revolving.redacted_public_signal_reference == "sha256:26e3bfbb8abd"
    assert revolving.reason_codes == (
        "market_research_consumer_credit_surprise_digest_stale_signal",
        "market_research_consumer_credit_surprise_digest_material_surprise",
        "market_research_consumer_credit_surprise_digest_thin_sources",
        "market_research_consumer_credit_surprise_digest_high_revision",
        "market_research_consumer_credit_surprise_digest_confirmation_gap",
    )

    nonrevolving = summary.rows[1]
    assert nonrevolving.digest_status == "watch"
    assert nonrevolving.signal_age_seconds == d("3600.000000")
    assert nonrevolving.surprise_delta == d("-4.000000")
    assert nonrevolving.confidence_decay_factor == d("0.800000")
    assert nonrevolving.final_confidence == d("0.680000")
    assert nonrevolving.redacted_public_signal_reference == "sha256:6ff7954f3c2f"
    assert nonrevolving.reason_codes == (
        "market_research_consumer_credit_surprise_digest_material_surprise",
        "market_research_consumer_credit_surprise_digest_confirmation_gap",
    )

    total = summary.rows[2]
    assert total.digest_status == "ready"
    assert total.signal_age_seconds == d("1500.000000")
    assert total.surprise_delta == d("0.500000")
    assert total.confidence_decay_factor == d("1.000000")
    assert total.final_confidence == d("0.920000")
    assert total.redacted_public_signal_reference == "public-consumer-credit-total"
    assert total.reason_codes == (
        "market_research_consumer_credit_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_credit_surprise_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_credit_surprise_digest_material_surprise",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_credit_surprise_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_credit_surprise_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_credit_surprise_digest_high_revision",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_credit_surprise_digest_ready",
            count=d("1.000000"),
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
        "private-credit-feed",
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
    ):
        assert token not in public


def test_consumer_credit_digest_empty_inputs_are_blocked_with_decimal_counts() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.signal_count == ZERO
    assert summary.rows == ()
    assert summary.average_surprise_score is None
    assert summary.max_signal_age_seconds is None
    assert summary.average_source_count is None
    assert summary.reason_code_counts == (
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_credit_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_consumer_credit_surprise_digest_no_inputs",
    )


def test_consumer_credit_digest_dataclasses_are_frozen_and_decimal_only() -> None:
    cfg = config()
    source = signal(observed_at=datetime(2026, 7, 3, 11, 30, tzinfo=timezone.utc))
    summary = report((source,), cfg=cfg)

    with pytest.raises(FrozenInstanceError):
        source.source_count = d("4.000000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].final_confidence = d("0.500000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.signal_count = d("2.000000")  # type: ignore[misc]

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
        "expected_credit_change",
        "actual_credit_change",
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
        (lambda: config(paper_only=False), "paper_only"),
        (lambda: config(report_only=False), "report_only"),
        (lambda: config(readonly=False), "readonly"),
        (lambda: config(min_source_count=2), "Decimal"),
        (lambda: config(max_signal_age_seconds=_DecimalSubclass("1")), "Decimal"),
        (lambda: signal(source_count=d("-1.000000")), "source_count"),
        (lambda: signal(surprise_score=d("1.500000")), "surprise_score"),
        (lambda: signal(public_signal_reference="wallet source"), "public_signal_reference"),
        (lambda: signal(signal_config_version=_StringSubclass("config-v0")), "signal_config_version"),
        (lambda: signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC)), "observed_at"),
        (
            lambda: signal(
                observed_at=datetime(2026, 7, 3, tzinfo=_NoneOffsetTimezone()),
            ),
            "timezone-aware",
        ),
        (
            lambda: report(
                (signal(),),
                generated_at=datetime(2026, 7, 3, tzinfo=_NoneOffsetTimezone()),
            ),
            "timezone-aware",
        ),
        (lambda: signal(expected_credit_change=1.0), "expected_credit_change"),
    ),
)
def test_consumer_credit_digest_validates_inputs_and_flags(
    factory: object,
    message: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        factory()


@pytest.mark.parametrize(
    "flag_name",
    ("paper_only", "report_only", "readonly"),
)
def test_consumer_credit_digest_rejects_false_report_only_flags(
    flag_name: str,
) -> None:
    good = report((signal(),))
    source = signal()
    instances = (
        config(),
        source,
        good.rows[0],
        good.reason_code_counts[0],
        good,
    )

    for instance in instances:
        with pytest.raises(ValueError, match=flag_name):
            replace(instance, **{flag_name: False})


def test_consumer_credit_digest_constructors_reject_noncanonical_ordering() -> None:
    finding_summary = report(
        (
            signal(
                surprise_score=d("0.040000"),
                confirmation_ratio=d("0.600000"),
            ),
        ),
    )
    row_reason_codes = finding_summary.rows[0].reason_codes
    report_reason_codes = finding_summary.reason_codes

    with pytest.raises(ValueError, match="reason_codes"):
        replace(finding_summary.rows[0], reason_codes=tuple(reversed(row_reason_codes)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            finding_summary.rows[0],
            reason_codes=row_reason_codes + (row_reason_codes[0],),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            finding_summary,
            reason_code_counts=tuple(reversed(finding_summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(finding_summary, reason_codes=tuple(reversed(report_reason_codes)))

    row_summary = report(
        (
            signal("condition_b", release_key="release.b", surprise_score=d("0.010000")),
            signal("condition_a", release_key="release.a", surprise_score=d("0.010000")),
        ),
    )
    assert tuple(row.condition_id for row in row_summary.rows) == (
        "condition_a",
        "condition_b",
    )
    with pytest.raises(ValueError, match="rows"):
        replace(row_summary, rows=tuple(reversed(row_summary.rows)))


@pytest.mark.parametrize(
    "flag_name",
    ("paper_only", "report_only", "readonly"),
)
def test_consumer_credit_digest_payload_rejects_false_report_only_flags(
    flag_name: str,
) -> None:
    payload = {
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    payload[flag_name] = False

    with pytest.raises(ValueError, match=flag_name):
        market_research_consumer_credit_surprise_digest_payload(payload)


def test_consumer_credit_digest_rejects_subclasses_and_inconsistent_reports() -> None:
    with pytest.raises(TypeError, match="subclassing"):

        class ConfigSubclass(MarketResearchConsumerCreditSurpriseDigestConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class SignalSubclass(MarketResearchConsumerCreditSurpriseDigestSignal):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class RowSubclass(MarketResearchConsumerCreditSurpriseDigestRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class ReasonCodeCountSubclass(
            MarketResearchConsumerCreditSurpriseDigestReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class ReportSubclass(MarketResearchConsumerCreditSurpriseDigestReport):
            pass

    good = report((signal(),))
    with pytest.raises(ValueError, match="count"):
        MarketResearchConsumerCreditSurpriseDigestReasonCodeCount(
            reason_code="market_research_consumer_credit_surprise_digest_no_inputs",
            count=ZERO,
            signal_ratio=ZERO,
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(good, reason_codes=("unexpected",))
    with pytest.raises(ValueError, match="config_version"):
        replace(good, config_version="unsupported-version")
    with pytest.raises(ValueError, match="supported reason codes"):
        replace(
            good.rows[0],
            reason_codes=("market_research_consumer_credit_surprise_digest_no_inputs",),
        )
    with pytest.raises(ValueError, match="signal_count"):
        replace(good, signal_count=d("99.000000"))


def test_consumer_credit_digest_payload_is_public_and_deterministic() -> None:
    summary = report(
        (
            signal("condition_b", release_key="release.b", surprise_score=d("0.100000")),
            signal("condition_a", release_key="release.a", surprise_score=d("0.100000")),
        ),
    )
    payload = market_research_consumer_credit_surprise_digest_payload(summary)

    assert payload == market_research_consumer_credit_surprise_digest_payload(summary)
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

    assert market_research_consumer_credit_surprise_digest_payload(payload) == payload
    dict_payload = market_research_consumer_credit_surprise_digest_payload(
        {
            "generated_at": GENERATED_AT,
            "signal_count": Decimal("2"),
            "paper_only": True,
            "report_only": True,
            "readonly": True,
            "rows": ({"source_count": Decimal("1")},),
        },
    )
    assert dict_payload["generated_at"] == "2026-07-03T16:00:00+00:00"
    assert dict_payload["signal_count"] == "2.000000"
    assert dict_payload["rows"] == [{"source_count": "1.000000"}]
    with pytest.raises(ValueError, match="public and redacted"):
        market_research_consumer_credit_surprise_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "redacted_public_signal_reference": "token-source",
            },
        )
    with pytest.raises(ValueError, match="report"):
        market_research_consumer_credit_surprise_digest_payload(object())


def test_consumer_credit_digest_module_has_no_durable_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_consumer_credit_surprise_digest.py"
    )
    tree = ast.parse(module_path.read_text())
    source = module_path.read_text(encoding="utf-8").lower()

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "supabase",
        "web3",
        "pathlib",
    }
    forbidden_call_names = {
        "open",
        "connect",
        "request",
        "urlopen",
        "create_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "place_order",
        "float",
    }
    for forbidden in (
        "auth",
        "wallet",
        "account",
        "order",
        "cancel",
        "replace",
        "database",
        "persist",
        "secret",
        "token",
        "private",
        "vendor",
        "https://",
        "http://",
        "market_slug",
        "question",
        "live trading",
        "durable store",
        "fast mode",
    ):
        assert forbidden not in source
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
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
