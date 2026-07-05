from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_initial_jobless_claims_surprise_digest import (
    DEFAULT_MARKET_RESEARCH_INITIAL_JOBLESS_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION,
    MarketResearchInitialJoblessClaimsSurpriseDigestConfig,
    MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount,
    MarketResearchInitialJoblessClaimsSurpriseDigestReport,
    MarketResearchInitialJoblessClaimsSurpriseDigestRow,
    MarketResearchInitialJoblessClaimsSurpriseDigestSignal,
    build_market_research_initial_jobless_claims_surprise_digest,
    market_research_initial_jobless_claims_surprise_digest_payload,
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
) -> MarketResearchInitialJoblessClaimsSurpriseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_INITIAL_JOBLESS_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
        ),
        "max_release_age_seconds": d("7200.000000"),
        "min_abs_surprise_claims": d("15000.000000"),
        "min_surprise_ratio": d("0.040000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchInitialJoblessClaimsSurpriseDigestConfig(**values)


def claims_signal(
    condition_id: str = "condition.claims.ready",
    *,
    claims_market_key: str = "us.initial-claims.ready",
    release_key: str = "dol.initial-claims.weekly",
    public_signal_reference: str = "dol-claims-public-release",
    released_at: datetime | None = None,
    forecast_claims: Decimal = d("225000.000000"),
    actual_claims: Decimal = d("245000.000000"),
    surprise_claims: Decimal = d("20000.000000"),
    surprise_ratio: Decimal = d("0.088889"),
    source_family_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "initial-jobless-claims-surprise-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchInitialJoblessClaimsSurpriseDigestSignal:
    return MarketResearchInitialJoblessClaimsSurpriseDigestSignal(
        condition_id=condition_id,
        claims_market_key=claims_market_key,
        release_key=release_key,
        public_signal_reference=public_signal_reference,
        released_at=released_at or GENERATED_AT - timedelta(minutes=30),
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
    cfg: MarketResearchInitialJoblessClaimsSurpriseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchInitialJoblessClaimsSurpriseDigestReport:
    return build_market_research_initial_jobless_claims_surprise_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_initial_jobless_claims_surprise_digest_reduces_redacts_and_sorts() -> None:
    summary = report(
        (
            claims_signal(
                "condition.claims.stale-soft",
                claims_market_key="us.initial-claims.stale-soft",
                release_key="dol.claims.stale-soft",
                public_signal_reference="https://labor.example/claims?token=secret-123",
                released_at=GENERATED_AT - timedelta(hours=4),
                forecast_claims=d("230000.000000"),
                actual_claims=d("238000.000000"),
                surprise_claims=d("8000.000000"),
                surprise_ratio=d("0.034783"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.450000"),
                base_confidence=d("0.900000"),
            ),
            claims_signal(
                "condition.claims.confirmation-gap",
                claims_market_key="us.initial-claims.confirmation-gap",
                release_key="dol.claims.confirmation-gap",
                public_signal_reference="wallet://private/claims-note",
                forecast_claims=d("220000.000000"),
                actual_claims=d("245000.000000"),
                surprise_claims=d("25000.000000"),
                surprise_ratio=d("0.113636"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                confirmation_ratio=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
            claims_signal(
                "condition.claims.ready",
                claims_market_key="us.initial-claims.ready",
                release_key="dol.claims.ready",
                public_signal_reference="dol-claims-public-release",
                forecast_claims=d("225000.000000"),
                actual_claims=d("245000.000000"),
                surprise_claims=d("20000.000000"),
                surprise_ratio=d("0.088889"),
                source_family_count=d("4.000000"),
                stale_source_ratio=d("0.050000"),
                confirmation_ratio=d("0.830000"),
                base_confidence=d("0.880000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchInitialJoblessClaimsSurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_INITIAL_JOBLESS_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_initial_jobless_claims_surprise_digest"
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
    assert summary.average_final_confidence == d("0.686667")
    assert summary.average_surprise_claims == d("17666.666667")
    assert summary.average_surprise_ratio == d("0.079103")
    assert summary.average_confirmation_ratio == d("0.610000")
    assert summary.max_release_age_seconds == d("14400.000000")
    assert tuple(row.claims_market_key for row in summary.rows) == (
        "us.initial-claims.stale-soft",
        "us.initial-claims.confirmation-gap",
        "us.initial-claims.ready",
    )

    blocked = summary.rows[0]
    assert blocked.digest_status == "blocked"
    assert blocked.release_age_seconds == d("14400.000000")
    assert blocked.confidence_decay_factor == d("0.500000")
    assert blocked.final_confidence == d("0.400000")
    assert blocked.redacted_public_signal_reference == "sha256:0cbc0bb3f2b4"
    assert blocked.reason_codes == (
        "market_research_initial_jobless_claims_surprise_digest_stale_release",
        "market_research_initial_jobless_claims_surprise_digest_low_absolute_surprise",
        "market_research_initial_jobless_claims_surprise_digest_low_surprise_ratio",
        "market_research_initial_jobless_claims_surprise_digest_source_family_gap",
        "market_research_initial_jobless_claims_surprise_digest_stale_source_ratio",
        "market_research_initial_jobless_claims_surprise_digest_confirmation_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.confidence_decay_factor == d("0.100000")
    assert watch.final_confidence == d("0.660000")
    assert watch.redacted_public_signal_reference == "sha256:b459f9894194"
    assert watch.reason_codes == (
        "market_research_initial_jobless_claims_surprise_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.880000")
    assert ready.redacted_public_signal_reference == "dol-claims-public-release"
    assert ready.reason_codes == (
        "market_research_initial_jobless_claims_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_initial_jobless_claims_surprise_digest_"
                "confirmation_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_initial_jobless_claims_surprise_digest_stale_release"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_initial_jobless_claims_surprise_digest_"
                "low_absolute_surprise"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_initial_jobless_claims_surprise_digest_"
                "low_surprise_ratio"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_initial_jobless_claims_surprise_digest_"
                "source_family_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_initial_jobless_claims_surprise_digest_"
                "stale_source_ratio"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_jobless_claims_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )


def test_empty_initial_jobless_claims_digest_is_watch_and_decimal_only() -> None:
    summary = report(())

    assert summary.digest_status == "watch"
    assert summary.recommended_next_step == (
        "watch_report_only_market_research_initial_jobless_claims_surprise_digest"
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
        MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_jobless_claims_surprise_digest_no_inputs",
            count=d("0.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_initial_jobless_claims_surprise_digest_no_inputs",
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


def test_initial_jobless_claims_digest_validates_types_flags_and_freezing() -> None:
    signal = claims_signal()
    summary = report((signal,))

    assert is_dataclass(MarketResearchInitialJoblessClaimsSurpriseDigestConfig)
    assert is_dataclass(MarketResearchInitialJoblessClaimsSurpriseDigestSignal)
    assert is_dataclass(MarketResearchInitialJoblessClaimsSurpriseDigestRow)
    assert is_dataclass(MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount)
    assert is_dataclass(MarketResearchInitialJoblessClaimsSurpriseDigestReport)
    frozen_config = config()
    with pytest.raises(FrozenInstanceError):
        frozen_config.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal.condition_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "BadSignal",
            (MarketResearchInitialJoblessClaimsSurpriseDigestSignal,),
            {},
        )

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(signal, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(config(), readonly=False)
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("claims-v0"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported-claims-v0")
    with pytest.raises(ValueError, match="max_release_age_seconds"):
        config(max_release_age_seconds=7200)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_abs_surprise_claims"):
        config(min_abs_surprise_claims=_DecimalSubclass("15000.000000"))
    with pytest.raises(ValueError, match="min_surprise_ratio"):
        config(min_surprise_ratio=d("1.000001"))
    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at="not-a-datetime")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        report((), generated_at=datetime(2026, 7, 3, 16, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        report(
            (),
            generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="released_at"):
        claims_signal(released_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="forecast_claims"):
        claims_signal(forecast_claims=Decimal("Infinity"))
    with pytest.raises(ValueError, match="actual_claims"):
        claims_signal(actual_claims=_DecimalSubclass("238000.000000"))
    with pytest.raises(ValueError, match="surprise_claims"):
        claims_signal(surprise_claims=d("-1.000000"))
    with pytest.raises(ValueError, match="condition_id"):
        claims_signal(condition_id=_StringSubclass("condition.subclass"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="iterable"):
        build_market_research_initial_jobless_claims_surprise_digest(
            "not-a-list",
            config=config(),
            generated_at=GENERATED_AT,
        )  # type: ignore[arg-type]
    with pytest.raises(
        ValueError,
        match="MarketResearchInitialJoblessClaimsSurpriseDigestSignal",
    ):
        report((object(),))
    with pytest.raises(ValueError, match="config"):
        build_market_research_initial_jobless_claims_surprise_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )

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
                MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
                    reason_code=summary.reason_code_counts[0].reason_code,
                    count=d("2.000000"),
                    signal_ratio=d("1.000000"),
                ),
            ),
        )


def test_initial_jobless_claims_payload_is_report_only_and_literal_safe() -> None:
    summary = report((claims_signal(),))
    payload = market_research_initial_jobless_claims_surprise_digest_payload(summary)

    assert payload["recommended_next_step"] == (
        "allow_report_only_market_research_initial_jobless_claims_surprise_digest"
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["rows"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["paper_only"] is True
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["rows"][0]["released_at"] == (
        GENERATED_AT - timedelta(minutes=30)
    ).isoformat()
    assert payload["signal_count"] == "1.000000"
    assert payload["rows"][0]["forecast_claims"] == "225000.000000"
    assert payload["rows"][0]["final_confidence"] == "0.860000"
    assert not any(
        isinstance(value, (Decimal, datetime, float)) for value in walk_values(payload)
    )

    public = repr(payload).lower()
    for token in (
        "secret-123",
        "labor.example",
        "https://",
        "private",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
        "network",
        "database",
        "wallet",
        "order",
        "token",
        "secret",
    ):
        assert token not in public


def test_initial_jobless_claims_signal_reference_is_redacted_before_storage() -> None:
    signal = claims_signal(
        public_signal_reference="https://labor.example/claims?token=secret-123",
    )

    assert signal.public_signal_reference == "sha256:0cbc0bb3f2b4"
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


def test_initial_jobless_claims_low_absolute_surprise_is_independent_reason() -> None:
    summary = report(
        (
            claims_signal(
                actual_claims=d("238000.000000"),
                surprise_claims=d("13000.000000"),
                surprise_ratio=d("0.057778"),
            ),
        ),
    )

    assert summary.digest_status == "watch"
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == d("1.000000")
    assert summary.low_absolute_surprise_signal_count == d("1.000000")
    assert summary.low_surprise_ratio_signal_count == ZERO
    assert summary.rows[0].confidence_decay_factor == d("0.100000")
    assert summary.rows[0].final_confidence == d("0.760000")
    assert summary.rows[0].reason_codes == (
        "market_research_initial_jobless_claims_surprise_digest_low_absolute_surprise",
    )


def test_initial_jobless_claims_sorting_is_deterministic_for_equal_status_and_age() -> None:
    summary = report(
        (
            claims_signal(
                "condition.z",
                claims_market_key="us.initial-claims.tie",
                release_key="release.z",
            ),
            claims_signal(
                "condition.a",
                claims_market_key="us.initial-claims.tie",
                release_key="release.a",
            ),
        ),
    )

    assert tuple(row.condition_id for row in summary.rows) == (
        "condition.a",
        "condition.z",
    )


def test_initial_jobless_claims_rows_and_counts_are_frozen_dataclasses() -> None:
    row = MarketResearchInitialJoblessClaimsSurpriseDigestRow(
        condition_id="condition.manual",
        claims_market_key="manual.claims",
        release_key="manual.release",
        digest_status="ready",
        released_at=GENERATED_AT,
        release_age_seconds=d("0.000000"),
        forecast_claims=d("225000.000000"),
        actual_claims=d("245000.000000"),
        surprise_claims=d("20000.000000"),
        surprise_ratio=d("0.088889"),
        source_family_count=d("3.000000"),
        stale_source_ratio=d("0.000000"),
        confirmation_ratio=d("0.900000"),
        base_confidence=d("0.850000"),
        confidence_decay_factor=d("0.000000"),
        final_confidence=d("0.850000"),
        redacted_public_signal_reference="manual-reference",
        reason_codes=(
            "market_research_initial_jobless_claims_surprise_digest_ready",
        ),
    )
    reason = MarketResearchInitialJoblessClaimsSurpriseDigestReasonCodeCount(
        reason_code="market_research_initial_jobless_claims_surprise_digest_ready",
        count=d("1.000000"),
        signal_ratio=d("1.000000"),
    )

    assert is_dataclass(row)
    assert is_dataclass(reason)
    with pytest.raises(FrozenInstanceError):
        row.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason.count = d("2.000000")  # type: ignore[misc]


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/"
        "market_research_initial_jobless_claims_surprise_digest.py",
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "aiohttp",
        "psycopg",
        "supabase",
        "sqlite",
        "sqlalchemy",
        "pathlib",
        "openai",
        "boto",
        "ccxt",
    )
    forbidden_call_or_attribute_names = (
        "connect",
        "execute",
        "fetch",
        "get",
        "post",
        "put",
        "delete",
        "request",
        "open",
        "read",
        "write",
        "mkdir",
        "unlink",
        "rename",
        "submit",
        "cancel",
        "order",
        "trade",
        "wallet",
        "broker",
        "account",
        "sign",
        "auth",
    )

    lowered_imports = tuple(name.lower() for name in imported_modules)
    lowered_surface = tuple(name.lower() for name in (*call_names, *attribute_names))
    assert not any(
        fragment in module_name
        for module_name in lowered_imports
        for fragment in forbidden_import_fragments
    )
    assert not any(name in forbidden_call_or_attribute_names for name in lowered_surface)
    assert "persist" not in source.lower()
    assert "database" not in source.lower()
    assert "advice" not in source.lower()


def walk_values(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in walk_values(nested))
    if isinstance(value, (list, tuple)):
        return tuple(item for nested in value for item in walk_values(nested))
    return (value,)
