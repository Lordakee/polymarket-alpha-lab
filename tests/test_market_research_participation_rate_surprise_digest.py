from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_participation_rate_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_PARTICIPATION_RATE_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchParticipationRateSurpriseDigestConfig,
    MarketResearchParticipationRateSurpriseDigestReasonCodeCount,
    MarketResearchParticipationRateSurpriseDigestReport,
    MarketResearchParticipationRateSurpriseDigestRow,
    MarketResearchParticipationRateSurpriseDigestSignal,
    build_market_research_participation_rate_surprise_digest,
    market_research_participation_rate_surprise_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 3, 16, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


class _MissingOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchParticipationRateSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_PARTICIPATION_RATE_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_source_count": d("2"),
        "material_surprise_threshold": d("0.025000"),
        "max_revision_ratio": d("0.150000"),
        "min_confirmation_ratio": d("0.650000"),
        "watch_confidence_threshold": d("0.700000"),
    }
    values.update(overrides)
    return MarketResearchParticipationRateSurpriseDigestConfig(**values)


def signal(
    condition_id: str = "condition_participation_rate",
    *,
    research_key: str = "research.participation_rate.bls",
    release_key: str = "employment.participation_rate.monthly",
    demographic_group: str = "headline",
    public_signal_reference: str = "public-bls-participation-rate",
    observed_at: datetime | None = None,
    expected_rate: Decimal = d("62.600000"),
    actual_rate: Decimal = d("62.500000"),
    surprise_score: Decimal = d("0.020000"),
    source_count: Decimal = d("3"),
    revision_ratio: Decimal = d("0.050000"),
    confirmation_ratio: Decimal = d("0.850000"),
    base_confidence: Decimal = d("0.900000"),
    signal_config_version: str = "participation-rate-signal-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchParticipationRateSurpriseDigestSignal:
    return MarketResearchParticipationRateSurpriseDigestSignal(
        condition_id=condition_id,
        research_key=research_key,
        release_key=release_key,
        demographic_group=demographic_group,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=30),
        expected_rate=expected_rate,
        actual_rate=actual_rate,
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
    cfg: MarketResearchParticipationRateSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchParticipationRateSurpriseDigestReport:
    return build_market_research_participation_rate_surprise_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_participation_rate_surprise_digest_reduces_and_sorts_deterministically() -> None:
    prime_age_signal = signal(
        "condition_prime_age",
        research_key="research.participation_rate.prime_age",
        release_key="employment.participation_rate.prime_age",
        demographic_group="prime_age",
        public_signal_reference=("https://vendor.example/participation?token=secret-123"),
        observed_at=GENERATED_AT - timedelta(hours=3),
        expected_rate=d("83.600000"),
        actual_rate=d("83.000000"),
        surprise_score=d("0.040000"),
        source_count=d("1"),
        revision_ratio=d("0.220000"),
        confirmation_ratio=d("0.400000"),
        base_confidence=d("0.880000"),
    )
    assert prime_age_signal.public_signal_reference == "sha256:e5a38c6e1834"
    assert "secret-123" not in repr(asdict(prime_age_signal)).lower()

    summary = report(
        (
            prime_age_signal,
            signal(
                "condition_headline",
                observed_at=datetime(2026, 7, 3, 11, 0, tzinfo=timezone(timedelta(hours=-4))),
                expected_rate=d("62.900000"),
                actual_rate=d("62.300000"),
                surprise_score=d("0.030000"),
                source_count=d("4"),
                revision_ratio=d("0.040000"),
                confirmation_ratio=d("0.500000"),
                base_confidence=d("0.850000"),
            ),
            signal(
                "condition_youth",
                research_key="research.participation_rate.youth",
                release_key="employment.participation_rate.youth",
                demographic_group="youth",
                public_signal_reference="public-youth-participation-rate",
                observed_at=GENERATED_AT - timedelta(minutes=20),
                expected_rate=d("37.400000"),
                actual_rate=d("37.100000"),
                surprise_score=d("0.015000"),
                source_count=d("3"),
                revision_ratio=d("0.050000"),
                confirmation_ratio=d("0.900000"),
                base_confidence=d("0.910000"),
            ),
        ),
        generated_at=datetime(2026, 7, 3, 12, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_PARTICIPATION_RATE_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_participation_rate_surprise_digest"
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
    assert summary.average_surprise_score == d("0.028333")
    assert summary.max_signal_age_seconds == d("10800.000000")
    assert summary.average_source_count == d("2.666667")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.condition_id for row in summary.rows) == (
        "condition_headline",
        "condition_prime_age",
        "condition_youth",
    )

    headline = summary.rows[0]
    assert headline.digest_status == "watch"
    assert headline.observed_at == GENERATED_AT - timedelta(hours=1)
    assert headline.observed_at.tzinfo is UTC
    assert headline.signal_age_seconds == d("3600.000000")
    assert headline.surprise_delta == d("-0.600000")
    assert headline.confidence_decay_factor == d("0.800000")
    assert headline.final_confidence == d("0.680000")
    assert headline.redacted_public_signal_reference == "public-bls-participation-rate"
    assert headline.reason_codes == (
        "market_research_participation_rate_surprise_digest_material_surprise",
        "market_research_participation_rate_surprise_digest_confirmation_gap",
    )

    prime_age = summary.rows[1]
    assert prime_age.digest_status == "blocked"
    assert prime_age.signal_age_seconds == d("10800.000000")
    assert prime_age.surprise_delta == d("-0.600000")
    assert prime_age.confidence_decay_factor == d("0.500000")
    assert prime_age.final_confidence == d("0.440000")
    assert prime_age.redacted_public_signal_reference == "sha256:e5a38c6e1834"
    assert prime_age.reason_codes == (
        "market_research_participation_rate_surprise_digest_stale_signal",
        "market_research_participation_rate_surprise_digest_material_surprise",
        "market_research_participation_rate_surprise_digest_thin_sources",
        "market_research_participation_rate_surprise_digest_high_revision",
        "market_research_participation_rate_surprise_digest_confirmation_gap",
    )

    youth = summary.rows[2]
    assert youth.digest_status == "ready"
    assert youth.signal_age_seconds == d("1200.000000")
    assert youth.surprise_delta == d("-0.300000")
    assert youth.confidence_decay_factor == d("1.000000")
    assert youth.final_confidence == d("0.910000")
    assert youth.reason_codes == (
        "market_research_participation_rate_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchParticipationRateSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_participation_rate_surprise_digest_confirmation_gap"
            ),
            count=d("2"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchParticipationRateSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_participation_rate_surprise_digest_material_surprise"
            ),
            count=d("2"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchParticipationRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_participation_rate_surprise_digest_stale_signal",
            count=d("1"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchParticipationRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_participation_rate_surprise_digest_thin_sources",
            count=d("1"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchParticipationRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_participation_rate_surprise_digest_high_revision",
            count=d("1"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchParticipationRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_participation_rate_surprise_digest_ready",
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
        "private-participation-feed",
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


def test_participation_rate_digest_empty_inputs_are_blocked_with_decimal_counts() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.signal_count == ZERO
    assert summary.rows == ()
    assert summary.average_surprise_score == ZERO
    assert summary.max_signal_age_seconds == ZERO
    assert summary.average_source_count == ZERO
    assert summary.reason_code_counts == (
        MarketResearchParticipationRateSurpriseDigestReasonCodeCount(
            reason_code="market_research_participation_rate_surprise_digest_no_inputs",
            count=d("1"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.reason_codes == (
        "market_research_participation_rate_surprise_digest_no_inputs",
    )

    payload = market_research_participation_rate_surprise_digest_payload(summary)
    assert payload["average_surprise_score"] == "0.000000"
    assert payload["max_signal_age_seconds"] == "0.000000"
    assert payload["average_source_count"] == "0.000000"


def test_participation_rate_digest_dataclasses_are_frozen_and_decimal_only() -> None:
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
        "expected_rate",
        "actual_rate",
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
        "average_source_count",
        "count",
        "signal_ratio",
    }
    for obj in (
        cfg,
        source,
        summary,
        summary.rows[0],
        summary.reason_code_counts[0],
    ):
        assert is_dataclass(obj)
        for field in fields(obj):
            value = getattr(obj, field.name)
            if field.name in numeric_public_fields and value is not None:
                assert type(value) is Decimal, (field.name, type(value))
            assert type(value) is not float, (field.name, value)

    payload = market_research_participation_rate_surprise_digest_payload(summary)
    json_public = repr(payload).lower()
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["expected_rate"] == "62.600000"  # type: ignore[index]
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "wallet" not in json_public
    assert "order" not in json_public


def test_participation_rate_digest_payload_requires_exact_report_dataclass() -> None:
    summary = report((signal(),))
    valid_payload = market_research_participation_rate_surprise_digest_payload(summary)

    assert valid_payload["paper_only"] is True
    assert valid_payload["signal_count"] == "1.000000"

    for raw_payload in (valid_payload, asdict(summary)):
        with pytest.raises(
            ValueError,
            match="report must be exactly MarketResearchParticipationRateSurpriseDigestReport",
        ):
            market_research_participation_rate_surprise_digest_payload(raw_payload)


def test_participation_rate_digest_validates_public_surface_and_phase_1_flags() -> None:
    with pytest.raises(TypeError, match="does not support subclassing"):
        class _SignalSubclass(MarketResearchParticipationRateSurpriseDigestSignal):
            pass

    with pytest.raises(TypeError, match="does not support subclassing"):
        config(config_version=_StringSubclass("participation-rate-surprise-digest-v0"))
    with pytest.raises(TypeError, match="does not support subclassing"):
        signal(condition_id=_StringSubclass("condition_alpha"))
    with pytest.raises(TypeError, match="does not support subclassing"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="utcoffset"):
        signal(
            observed_at=datetime(
                2026,
                7,
                3,
                16,
                0,
                tzinfo=_MissingOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        signal(observed_at=datetime(2026, 7, 3, 16, 0))
    with pytest.raises(TypeError, match="does not support subclassing"):
        signal(surprise_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        signal(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        report((signal(readonly=False),))
    with pytest.raises(ValueError, match="unique condition_id"):
        report((signal("condition_dup"), signal("condition_dup")))
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        report((signal(observed_at=GENERATED_AT + timedelta(seconds=1)),))
    with pytest.raises(ValueError, match="public_signal_reference"):
        signal(public_signal_reference="private-participation-feed-token")
    with pytest.raises(ValueError, match="inputs must contain"):
        report((object(),))


def test_participation_rate_digest_module_avoids_forbidden_capabilities() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_participation_rate_surprise_digest.py",
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    forbidden_import_roots = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "urllib",
        "web3",
    }
    imports: set[str] = set()
    call_names: set[str] = set()
    string_literals: list[str] = []
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
        elif isinstance(node, ast.Call):
            target = node.func
            if isinstance(target, ast.Name):
                call_names.add(target.id)
            elif isinstance(target, ast.Attribute):
                call_names.add(target.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, str):
            string_literals.append(node.value.lower())

    assert imports.isdisjoint(forbidden_import_roots)
    assert call_names.isdisjoint({"open", "connect", "urlopen", "request"})
    joined_strings = "\n".join(string_literals)
    for forbidden in (
        "live trading",
        "auth",
        "wallet",
        "order placement",
        "order cancel",
        "order replace",
    ):
        assert forbidden not in joined_strings


def test_participation_rate_manual_public_records_reject_noncanonical_ordering() -> None:
    summary = report(
        (
            signal(
                "condition_prime_age",
                research_key="research.participation_rate.prime_age",
                release_key="employment.participation_rate.prime_age",
                demographic_group="prime_age",
                observed_at=GENERATED_AT - timedelta(hours=3),
                surprise_score=d("0.040000"),
                source_count=d("1"),
                revision_ratio=d("0.220000"),
                confirmation_ratio=d("0.400000"),
            ),
            signal(
                "condition_headline",
                observed_at=GENERATED_AT - timedelta(minutes=30),
                surprise_score=d("0.030000"),
                confirmation_ratio=d("0.500000"),
            ),
        ),
    )
    multi_reason_row = summary.rows[1]

    with pytest.raises(ValueError, match="reason_codes must use deterministic ordering"):
        replace(
            multi_reason_row,
            reason_codes=tuple(reversed(multi_reason_row.reason_codes)),
        )
    with pytest.raises(ValueError, match="reason_codes must use unique reason codes"):
        replace(
            multi_reason_row,
            reason_codes=multi_reason_row.reason_codes + (multi_reason_row.reason_codes[0],),
        )
    with pytest.raises(ValueError, match="rows must use deterministic ordering"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(
        ValueError,
        match="reason_code_counts must use deterministic ordering",
    ):
        replace(
            summary,
            reason_code_counts=tuple(reversed(summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes must use deterministic ordering"):
        replace(summary, reason_codes=tuple(reversed(summary.reason_codes)))


def test_participation_rate_digest_rejects_inconsistent_manual_dataclasses() -> None:
    with pytest.raises(ValueError, match="ready rows must use ready reason"):
        MarketResearchParticipationRateSurpriseDigestRow(
            condition_id="condition_manual",
            research_key="research.participation_rate.manual",
            release_key="employment.participation_rate.manual",
            demographic_group="manual",
            digest_status="ready",
            observed_at=GENERATED_AT,
            signal_age_seconds=d("0"),
            expected_rate=d("62.600000"),
            actual_rate=d("62.000000"),
            surprise_delta=d("-0.600000"),
            surprise_score=d("0.030000"),
            source_count=d("3"),
            revision_ratio=d("0.050000"),
            confirmation_ratio=d("0.900000"),
            base_confidence=d("0.900000"),
            confidence_decay_factor=d("1"),
            final_confidence=d("0.900000"),
            redacted_public_signal_reference="public-manual",
            signal_config_version="participation-rate-signal-v0",
            reason_codes=(
                "market_research_participation_rate_surprise_digest_material_surprise",
            ),
        )
