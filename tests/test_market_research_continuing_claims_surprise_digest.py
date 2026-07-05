from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_continuing_claims_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_CONTINUING_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchContinuingClaimsSurpriseDigestConfig,
    MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount,
    MarketResearchContinuingClaimsSurpriseDigestReport,
    MarketResearchContinuingClaimsSurpriseDigestRow,
    MarketResearchContinuingClaimsSurpriseDigestSignal,
    build_market_research_continuing_claims_surprise_digest,
    market_research_continuing_claims_surprise_digest_payload,
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

    def tzname(self, dt: datetime | None) -> str:
        return "none-offset"


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchContinuingClaimsSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_CONTINUING_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_release_age_seconds": d("10800.000000"),
        "min_abs_surprise_claims": d("50000.000000"),
        "min_surprise_ratio": d("0.030000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchContinuingClaimsSurpriseDigestConfig(**values)


def claims_signal(
    condition_id: str = "condition.continuing-claims.ready",
    *,
    claims_market_key: str = "us.continuing-claims.ready",
    release_key: str = "dol.continuing-claims.weekly",
    public_signal_reference: str = "dol-continuing-claims-public-release",
    released_at: datetime | None = None,
    forecast_claims: Decimal = d("1850000.000000"),
    actual_claims: Decimal = d("1925000.000000"),
    surprise_claims: Decimal = d("75000.000000"),
    surprise_ratio: Decimal = d("0.040541"),
    source_family_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "continuing-claims-surprise-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchContinuingClaimsSurpriseDigestSignal:
    return MarketResearchContinuingClaimsSurpriseDigestSignal(
        condition_id=condition_id,
        claims_market_key=claims_market_key,
        release_key=release_key,
        public_signal_reference=public_signal_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=45),
        forecast_claims=forecast_claims,
        actual_claims=actual_claims,
        surprise_claims=surprise_claims,
        surprise_ratio=surprise_ratio,
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
    cfg: MarketResearchContinuingClaimsSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchContinuingClaimsSurpriseDigestReport:
    return build_market_research_continuing_claims_surprise_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_continuing_claims_surprise_digest_reduces_redacts_and_sorts() -> None:
    summary = report(
        (
            claims_signal(
                "condition.continuing-claims.ready",
                claims_market_key="us.continuing-claims.ready",
                release_key="dol.continuing-claims.ready",
                public_signal_reference="dol-continuing-claims-public-release",
                forecast_claims=d("1850000.000000"),
                actual_claims=d("1935000.000000"),
                surprise_claims=d("85000.000000"),
                surprise_ratio=d("0.045946"),
                source_family_count=d("4.000000"),
                stale_source_ratio=d("0.050000"),
                confirmation_ratio=d("0.830000"),
                base_confidence=d("0.880000"),
            ),
            claims_signal(
                "condition.continuing-claims.confirmation-gap",
                claims_market_key="us.continuing-claims.confirmation-gap",
                release_key="dol.continuing-claims.confirmation-gap",
                public_signal_reference="wallet://private/continuing-claims-note",
                forecast_claims=d("1840000.000000"),
                actual_claims=d("1915000.000000"),
                surprise_claims=d("75000.000000"),
                surprise_ratio=d("0.040761"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                confirmation_ratio=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
            claims_signal(
                "condition.continuing-claims.stale-soft",
                claims_market_key="us.continuing-claims.stale-soft",
                release_key="dol.continuing-claims.stale-soft",
                public_signal_reference=(
                    "https://labor.example/continuing-claims?token=secret-123"
                ),
                released_at=GENERATED_AT - timedelta(hours=5),
                forecast_claims=d("1860000.000000"),
                actual_claims=d("1895000.000000"),
                surprise_claims=d("35000.000000"),
                surprise_ratio=d("0.018817"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.450000"),
                base_confidence=d("0.900000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchContinuingClaimsSurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_CONTINUING_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_continuing_claims_surprise_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_release_signal_count == d("1.000000")
    assert summary.low_absolute_surprise_signal_count == d("1.000000")
    assert summary.low_surprise_ratio_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.confirmation_gap_signal_count == d("2.000000")
    assert summary.total_confidence_decay == d("0.600000")
    assert summary.average_final_confidence == d("0.646667")
    assert summary.average_surprise_claims == d("65000.000000")
    assert summary.average_surprise_ratio == d("0.035175")
    assert summary.average_confirmation_ratio == d("0.610000")
    assert summary.max_release_age_seconds == d("18000.000000")
    assert tuple(row.claims_market_key for row in summary.rows) == (
        "us.continuing-claims.stale-soft",
        "us.continuing-claims.confirmation-gap",
        "us.continuing-claims.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.release_age_seconds == d("18000.000000")
    assert blocked.confidence_decay_factor == d("0.500000")
    assert blocked.final_confidence == d("0.400000")
    assert blocked.redacted_public_signal_reference == "sha256:825adc5faf05"
    assert blocked.reason_codes == (
        "market_research_continuing_claims_surprise_digest_stale_release",
        "market_research_continuing_claims_surprise_digest_low_absolute_surprise",
        "market_research_continuing_claims_surprise_digest_low_surprise_ratio",
        "market_research_continuing_claims_surprise_digest_source_family_gap",
        "market_research_continuing_claims_surprise_digest_stale_source_ratio",
        "market_research_continuing_claims_surprise_digest_confirmation_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.confidence_decay_factor == d("0.100000")
    assert watch.final_confidence == d("0.660000")
    assert watch.redacted_public_signal_reference == "sha256:15af540a1f22"
    assert watch.reason_codes == (
        "market_research_continuing_claims_surprise_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.880000")
    assert ready.redacted_public_signal_reference == (
        "dol-continuing-claims-public-release"
    )
    assert ready.reason_codes == (
        "market_research_continuing_claims_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_continuing_claims_surprise_digest_confirmation_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_continuing_claims_surprise_digest_stale_release"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_continuing_claims_surprise_digest_"
                "low_absolute_surprise"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_continuing_claims_surprise_digest_low_surprise_ratio"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_continuing_claims_surprise_digest_source_family_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_continuing_claims_surprise_digest_stale_source_ratio"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_continuing_claims_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )


def test_empty_continuing_claims_digest_is_watch_and_decimal_only() -> None:
    summary = report(())

    assert summary.digest_status == "watch"
    assert summary.recommended_next_step == (
        "watch_report_only_market_research_continuing_claims_surprise_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.average_final_confidence is None
    assert summary.average_surprise_claims is None
    assert summary.average_surprise_ratio is None
    assert summary.average_confirmation_ratio is None
    assert summary.max_release_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_continuing_claims_surprise_digest_no_inputs",
            count=d("0.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_continuing_claims_surprise_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    public_values = asdict(summary)
    numeric_or_countish = (
        "age",
        "claims",
        "count",
        "ratio",
        "confidence",
        "decay",
        "seconds",
    )
    for name, value in public_values.items():
        if any(fragment in name for fragment in numeric_or_countish):
            if isinstance(value, (dict, list, tuple)):
                continue
            assert isinstance(value, Decimal) or value is None, (name, value)


def test_continuing_claims_digest_validates_types_flags_and_freezing() -> None:
    signal = claims_signal()
    summary = report((signal,))

    assert is_dataclass(MarketResearchContinuingClaimsSurpriseDigestConfig)
    assert is_dataclass(MarketResearchContinuingClaimsSurpriseDigestSignal)
    assert is_dataclass(MarketResearchContinuingClaimsSurpriseDigestRow)
    assert is_dataclass(MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount)
    assert is_dataclass(MarketResearchContinuingClaimsSurpriseDigestReport)
    frozen_config = config()
    with pytest.raises(FrozenInstanceError):
        frozen_config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal.condition_id = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("2.000000")  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadSignal",
            (MarketResearchContinuingClaimsSurpriseDigestSignal,),
            {},
        )

    false_flag_cases = (
        (config(), "paper_only"),
        (config(), "report_only"),
        (config(), "readonly"),
        (signal, "paper_only"),
        (signal, "report_only"),
        (signal, "readonly"),
        (summary.rows[0], "paper_only"),
        (summary.rows[0], "report_only"),
        (summary.rows[0], "readonly"),
        (summary.reason_code_counts[0], "paper_only"),
        (summary.reason_code_counts[0], "report_only"),
        (summary.reason_code_counts[0], "readonly"),
        (summary, "paper_only"),
        (summary, "report_only"),
        (summary, "readonly"),
    )
    for value, flag_name in false_flag_cases:
        with pytest.raises(ValueError, match=flag_name):
            replace(value, **{flag_name: False})

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("claims-v0"))
    with pytest.raises(ValueError, match="max_release_age_seconds"):
        config(max_release_age_seconds=10800)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_abs_surprise_claims"):
        config(min_abs_surprise_claims=_DecimalSubclass("50000.000000"))
    with pytest.raises(ValueError, match="min_surprise_ratio"):
        config(min_surprise_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at="not-a-datetime")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="released_at"):
        claims_signal(released_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="forecast_claims"):
        claims_signal(forecast_claims=Decimal("Infinity"))
    with pytest.raises(ValueError, match="actual_claims"):
        claims_signal(actual_claims=_DecimalSubclass("1925000.000000"))
    with pytest.raises(ValueError, match="surprise_claims"):
        claims_signal(surprise_claims=d("-1.000000"))
    with pytest.raises(ValueError, match="condition_id"):
        claims_signal(condition_id=_StringSubclass("condition.subclass"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="iterable"):
        build_market_research_continuing_claims_surprise_digest(
            "not-a-list",
            config=config(),
            generated_at=GENERATED_AT,
        )  # type: ignore[arg-type]
    with pytest.raises(
        ValueError,
        match="MarketResearchContinuingClaimsSurpriseDigestSignal",
    ):
        report((object(),))


def test_continuing_claims_payload_is_report_only_and_literal_safe() -> None:
    summary = report((claims_signal(),))
    payload = market_research_continuing_claims_surprise_digest_payload(summary)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["paper_only"] is True
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["rows"][0]["released_at"] == (
        GENERATED_AT - timedelta(minutes=45)
    ).isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["final_confidence"] == "0.860000"
    assert not any(isinstance(value, float) for value in walk_values(payload))

    public = repr(payload).lower()
    for token in (
        "secret-123",
        "labor.example",
        "https://",
        "private",
        "auth",
        "broker",
        "wallet",
        "order",
        "cancel",
        "replace",
    ):
        assert token not in public


def test_continuing_claims_signal_reference_is_redacted_before_storage() -> None:
    signal = claims_signal(
        public_signal_reference="https://labor.example/continuing-claims?token=secret-123",
    )

    assert signal.public_signal_reference == "sha256:825adc5faf05"
    public = repr(signal).lower()
    for token in (
        "secret-123",
        "labor.example",
        "https://",
        "private",
        "wallet",
        "token",
        "secret",
    ):
        assert token not in public


def test_continuing_claims_rejects_timezone_without_offset() -> None:
    non_offset_time = datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone())

    with pytest.raises(ValueError, match="timezone-aware"):
        report((), generated_at=non_offset_time)
    with pytest.raises(ValueError, match="timezone-aware"):
        claims_signal(released_at=non_offset_time)


def test_continuing_claims_report_rejects_inconsistent_manual_counts() -> None:
    summary = report((claims_signal(),))
    ready_reason = summary.reason_code_counts[0].reason_code

    with pytest.raises(ValueError, match="ready_signal_count"):
        replace(
            summary,
            ready_signal_count=ZERO,
            watch_signal_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            summary,
            reason_code_counts=(
                MarketResearchContinuingClaimsSurpriseDigestReasonCodeCount(
                    reason_code=ready_reason,
                    count=d("2.000000"),
                    signal_ratio=d("1.000000"),
                ),
            ),
        )


def test_continuing_claims_public_surface_excludes_forbidden_domains() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/market_research_continuing_claims_surprise_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)
    forbidden_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "socket",
        "Session",
        "post",
        "put",
        "delete",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "place_order",
        "cancel_order",
        "replace_order",
    }
    forbidden_import_roots = {
        "http",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "web3",
        "eth_account",
    }
    forbidden_literals = {
        "place_order",
        "cancel_order",
        "replace_order",
        "private_key",
        "wallet",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            name = ""
            if isinstance(func, ast.Name):
                name = func.id
            elif isinstance(func, ast.Attribute):
                name = func.attr
            assert name not in forbidden_calls
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [alias.name for alias in node.names]
            else:
                modules = [node.module or ""]
            for module in modules:
                assert module.split(".")[0] not in forbidden_import_roots
        if isinstance(node, ast.Constant) and isinstance(node.value, str):
            lowered = node.value.lower()
            for literal in forbidden_literals:
                assert literal not in lowered


def walk_values(value: object) -> tuple[object, ...]:
    values: list[object] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(walk_values(item))
    elif isinstance(value, (list, tuple)):
        for item in value:
            values.extend(walk_values(item))
    return tuple(values)
