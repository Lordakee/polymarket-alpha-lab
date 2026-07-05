from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_core_pce_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_CORE_PCE_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchCorePceSurpriseDigestConfig,
    MarketResearchCorePceSurpriseDigestReasonCodeCount,
    MarketResearchCorePceSurpriseDigestReport,
    MarketResearchCorePceSurpriseDigestRow,
    MarketResearchCorePceSurpriseDigestSignal,
    build_market_research_core_pce_surprise_digest,
    market_research_core_pce_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 14, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchCorePceSurpriseDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_CORE_PCE_SURPRISE_DIGEST_CONFIG_VERSION,
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2.000000"),
        "material_surprise_threshold": d("0.050000"),
        "max_revision_ratio": d("0.200000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchCorePceSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_core_pce",
    *,
    research_key: str = "research.core_pce.monthly",
    release_key: str = "core_pce.monthly.latest",
    inflation_measure: str = "core_pce_monthly",
    public_signal_reference: str = "public-core-pce-release",
    observed_at: datetime | None = None,
    expected_inflation_rate: Decimal = d("0.002000"),
    actual_inflation_rate: Decimal = d("0.004000"),
    surprise_score: Decimal = d("0.060000"),
    source_count: Decimal = d("3.000000"),
    revision_ratio: Decimal = d("0.050000"),
    confirmation_ratio: Decimal = d("0.850000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "core-pce-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchCorePceSurpriseDigestSignal:
    return MarketResearchCorePceSurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        inflation_measure=inflation_measure,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=20),
        expected_inflation_rate=expected_inflation_rate,
        actual_inflation_rate=actual_inflation_rate,
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
    cfg: MarketResearchCorePceSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchCorePceSurpriseDigestReport:
    return build_market_research_core_pce_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_core_pce_surprise_digest_reduces_and_sorts_deterministically() -> None:
    summary = report(
        (
            signal(
                "condition_supercore",
                research_key="research.core_pce.supercore",
                release_key="core_pce.supercore.services",
                inflation_measure="supercore_services",
                public_signal_reference="https://vendor.example/core-pce?token=secret-123",
                observed_at=GENERATED_AT - timedelta(hours=3),
                expected_inflation_rate=d("0.003000"),
                actual_inflation_rate=d("0.007000"),
                surprise_score=d("0.090000"),
                source_count=d("1.000000"),
                revision_ratio=d("0.350000"),
                confirmation_ratio=d("0.420000"),
                base_confidence=d("0.880000"),
            ),
            signal(
                "condition_trimmed_mean",
                research_key="research.core_pce.trimmed_mean",
                release_key="core_pce.trimmed_mean",
                inflation_measure="trimmed_mean",
                public_signal_reference="public-trimmed-mean-pce",
                observed_at=GENERATED_AT - timedelta(minutes=25),
                expected_inflation_rate=d("0.002500"),
                actual_inflation_rate=d("0.002000"),
                surprise_score=d("0.010000"),
                source_count=d("3.000000"),
                revision_ratio=d("0.040000"),
                confirmation_ratio=d("0.900000"),
                base_confidence=d("0.920000"),
            ),
            signal(
                "condition-monthly-core-pce",
                research_key="research.core_pce.monthly",
                release_key="core_pce.monthly.latest",
                inflation_measure="core_pce_monthly",
                public_signal_reference="private-core-pce-feed",
                observed_at=GENERATED_AT - timedelta(hours=1),
                expected_inflation_rate=d("0.002000"),
                actual_inflation_rate=d("0.005500"),
                surprise_score=d("0.070000"),
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
        DEFAULT_MARKET_RESEARCH_CORE_PCE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_core_pce_surprise_digest"
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
    assert summary.average_surprise_score == d("0.056667")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.release_key for row in summary.rows) == (
        "core_pce.supercore.services",
        "core_pce.monthly.latest",
        "core_pce.trimmed_mean",
    )

    supercore = summary.rows[0]
    assert supercore.digest_status == "blocked"
    assert supercore.signal_age_seconds == d("10800.000000")
    assert supercore.surprise_delta == d("0.004000")
    assert supercore.surprise_ratio == d("1.333333")
    assert supercore.confidence_decay_factor == d("0.400000")
    assert supercore.final_confidence == d("0.352000")
    assert supercore.redacted_public_signal_reference == "sha256:d5f03b3c410e"
    assert supercore.reason_codes == (
        "market_research_core_pce_surprise_digest_stale_signal",
        "market_research_core_pce_surprise_digest_material_surprise",
        "market_research_core_pce_surprise_digest_thin_sources",
        "market_research_core_pce_surprise_digest_high_revision",
        "market_research_core_pce_surprise_digest_confirmation_gap",
    )

    monthly = summary.rows[1]
    assert monthly.digest_status == "watch"
    assert monthly.signal_age_seconds == d("3600.000000")
    assert monthly.surprise_delta == d("0.003500")
    assert monthly.surprise_ratio == d("1.750000")
    assert monthly.confidence_decay_factor == d("0.800000")
    assert monthly.final_confidence == d("0.680000")
    assert monthly.redacted_public_signal_reference == "sha256:de2953e9cd12"
    assert monthly.reason_codes == (
        "market_research_core_pce_surprise_digest_material_surprise",
        "market_research_core_pce_surprise_digest_confirmation_gap",
    )

    trimmed_mean = summary.rows[2]
    assert trimmed_mean.digest_status == "ready"
    assert trimmed_mean.signal_age_seconds == d("1500.000000")
    assert trimmed_mean.surprise_delta == d("-0.000500")
    assert trimmed_mean.surprise_ratio == d("-0.200000")
    assert trimmed_mean.confidence_decay_factor == d("1.000000")
    assert trimmed_mean.final_confidence == d("0.920000")
    assert trimmed_mean.redacted_public_signal_reference == "public-trimmed-mean-pce"
    assert trimmed_mean.reason_codes == (
        "market_research_core_pce_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_material_surprise",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_thin_sources",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_high_revision",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_ready",
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
        "private-core-pce-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "wallet",
        "account",
        "create_order",
        "submit_order",
        "cancel_order",
        "place_order",
    ):
        assert token not in public


def test_core_pce_digest_empty_inputs_are_blocked_with_decimal_counts() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.signal_count == ZERO
    assert summary.rows == ()
    assert summary.average_surprise_score is None
    assert summary.max_signal_age_seconds is None
    assert summary.average_source_count is None
    assert summary.reason_code_counts == (
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_core_pce_surprise_digest_no_inputs",
    )


def test_core_pce_digest_dataclasses_are_frozen_and_decimal_only() -> None:
    cfg = config()
    source = signal(observed_at=datetime(2026, 7, 3, 10, 30, tzinfo=timezone.utc))
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
        "expected_inflation_rate",
        "actual_inflation_rate",
        "surprise_score",
        "source_count",
        "revision_ratio",
        "confirmation_ratio",
        "base_confidence",
        "signal_age_seconds",
        "surprise_delta",
        "surprise_ratio",
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
        (lambda: signal(source_count=d("-1.000000")), "source_count"),
        (lambda: signal(surprise_score=d("1.500000")), "surprise_score"),
        (lambda: signal(public_signal_reference="wallet source"), "public_signal_reference"),
        (lambda: signal(condition_id="condition-order-flow"), "condition_id"),
        (lambda: signal(research_key="research.trade.intent"), "research_key"),
        (lambda: signal(release_key="release.submit.intent"), "release_key"),
        (lambda: signal(inflation_measure="wallet_measure"), "inflation_measure"),
        (lambda: signal(signal_config_version=_StringSubclass("config-v0")), "signal_config_version"),
        (lambda: signal(signal_config_version="core-pce-secret-config"), "signal_config_version"),
        (lambda: signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC)), "observed_at"),
        (lambda: signal(observed_at=datetime(2026, 7, 3, 10, 30)), "observed_at"),
        (
            lambda: signal(
                observed_at=datetime(
                    2026,
                    7,
                    3,
                    10,
                    30,
                    tzinfo=_NoneOffsetTz(),
                ),
            ),
            "observed_at",
        ),
        (
            lambda: report(
                (signal(observed_at=GENERATED_AT + timedelta(microseconds=1)),),
            ),
            "observed_at",
        ),
        (lambda: signal(expected_inflation_rate=_DecimalSubclass("0.002000")), "Decimal"),
        (lambda: signal(actual_inflation_rate=1), "Decimal"),
        (lambda: signal(base_confidence=0.7), "Decimal"),
    ),
)
def test_core_pce_digest_validates_inputs_and_flags(
    factory: object,
    message: str,
) -> None:
    with pytest.raises((TypeError, ValueError), match=message):
        factory()


def test_core_pce_digest_rejects_subclasses_and_inconsistent_reports() -> None:
    with pytest.raises(TypeError, match="subclassing"):
        class ConfigSubclass(MarketResearchCorePceSurpriseDigestConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class SignalSubclass(MarketResearchCorePceSurpriseDigestSignal):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class RowSubclass(MarketResearchCorePceSurpriseDigestRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReasonCodeCountSubclass(
            MarketResearchCorePceSurpriseDigestReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):
        class ReportSubclass(MarketResearchCorePceSurpriseDigestReport):
            pass

    good = report((signal(),))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(good, reason_codes=("unexpected",))
    with pytest.raises(ValueError, match="signal_count"):
        replace(good, signal_count=d("99.000000"))
    with pytest.raises(ValueError, match="count"):
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )
    with pytest.raises(ValueError, match="count"):
        MarketResearchCorePceSurpriseDigestReasonCodeCount(
            reason_code="market_research_core_pce_surprise_digest_ready",
            count=d("1.500000"),
            signal_ratio=ZERO,
        )


def test_core_pce_digest_public_constructors_reject_noncanonical_ordering() -> None:
    row_with_multiple_reasons = report(
        (signal(confirmation_ratio=d("0.600000")),),
    ).rows[0]
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row_with_multiple_reasons,
            reason_codes=tuple(reversed(row_with_multiple_reasons.reason_codes)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            row_with_multiple_reasons,
            reason_codes=(
                *row_with_multiple_reasons.reason_codes,
                row_with_multiple_reasons.reason_codes[0],
            ),
        )

    summary = report(
        (
            signal(
                "condition_b",
                release_key="release.b",
                surprise_score=d("0.010000"),
            ),
            signal(
                "condition_a",
                release_key="release.a",
                surprise_score=d("0.100000"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(summary, reason_code_counts=tuple(reversed(summary.reason_code_counts)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))
    with pytest.raises(ValueError, match="reason_codes"):
        replace(summary, reason_codes=(*summary.reason_codes, summary.reason_codes[0]))


def test_core_pce_digest_payload_is_public_and_deterministic() -> None:
    summary = report(
        (
            signal("condition_b", release_key="release.b", surprise_score=d("0.100000")),
            signal("condition_a", release_key="release.a", surprise_score=d("0.100000")),
        ),
    )
    payload = market_research_core_pce_surprise_digest_payload(summary)

    assert payload == market_research_core_pce_surprise_digest_payload(summary)
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
    assert "create_order" not in repr(payload).lower()
    assert "submit_order" not in repr(payload).lower()
    assert "cancel_order" not in repr(payload).lower()

    assert market_research_core_pce_surprise_digest_payload(payload) == payload
    with pytest.raises(ValueError, match="report"):
        market_research_core_pce_surprise_digest_payload(object())


def test_core_pce_digest_payload_rejects_public_float_int_and_secret_dicts() -> None:
    assert market_research_core_pce_surprise_digest_payload(
        {"signal_count": d("1")},
    ) == {"signal_count": "1.000000"}
    with pytest.raises(TypeError, match="Decimal"):
        market_research_core_pce_surprise_digest_payload({"signal_count": 1})
    with pytest.raises(TypeError, match="Decimal"):
        market_research_core_pce_surprise_digest_payload({"rows": [{"surprise_score": 0.1}]})
    with pytest.raises(TypeError, match="Decimal"):
        market_research_core_pce_surprise_digest_payload(
            {"signal_count": _DecimalSubclass("1.000000")},
        )
    with pytest.raises(ValueError, match="paper_only"):
        market_research_core_pce_surprise_digest_payload(
            {"paper_only": False, "report_only": True, "readonly": True},
        )
    with pytest.raises(ValueError, match="public"):
        market_research_core_pce_surprise_digest_payload(
            {"wallet_reference": "redacted-reference"},
        )
    with pytest.raises(ValueError, match="public"):
        market_research_core_pce_surprise_digest_payload(
            {"redacted_public_signal_reference": "token=secret-123"},
        )


def test_core_pce_digest_payload_revalidates_mutated_public_report_tree() -> None:
    mutated_report_flag = report((signal(),))
    object.__setattr__(mutated_report_flag, "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_core_pce_surprise_digest_payload(mutated_report_flag)

    mutated_row_flag = report((signal(),))
    object.__setattr__(mutated_row_flag.rows[0], "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_core_pce_surprise_digest_payload(mutated_row_flag)

    mutated_numeric = report((signal(),))
    object.__setattr__(mutated_numeric, "signal_count", 1)
    with pytest.raises((TypeError, ValueError), match="Decimal|signal_count"):
        market_research_core_pce_surprise_digest_payload(mutated_numeric)

    mutated_reference = report((signal(),))
    object.__setattr__(
        mutated_reference.rows[0],
        "redacted_public_signal_reference",
        "token=secret-123",
    )
    with pytest.raises(ValueError, match="public|redacted"):
        market_research_core_pce_surprise_digest_payload(mutated_reference)


def test_core_pce_digest_rejects_inconsistent_row_confidence() -> None:
    good = report((signal(),)).rows[0]
    with pytest.raises(ValueError, match="final_confidence"):
        replace(good, final_confidence=d("0.123456"))


def test_core_pce_digest_module_has_no_durable_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_core_pce_surprise_digest.py"
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
        "replace_order",
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
