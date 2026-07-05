from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from types import ModuleType

import pytest


MODULE_NAME = "polymarket_alpha_lab.market_research_initial_claims_surprise_digest"
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


def digest() -> ModuleType:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"{MODULE_NAME} must exist")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = digest()
    values = {
        "config_version": (
            module.DEFAULT_MARKET_RESEARCH_INITIAL_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
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
    return module.MarketResearchInitialClaimsSurpriseDigestConfig(**values)


def claims_signal(
    condition_id: str = "condition.initial-claims.ready",
    *,
    claims_market_key: str = "us.initial-claims.ready",
    release_key: str = "dol.initial-claims.weekly",
    public_signal_reference: str = "dol-initial-claims-public-release",
    released_at: datetime | None = None,
    forecast_claims: Decimal = d("225000.000000"),
    actual_claims: Decimal = d("245000.000000"),
    surprise_claims: Decimal = d("20000.000000"),
    surprise_ratio: Decimal = d("0.088889"),
    source_family_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.860000"),
    signal_config_version: str = "initial-claims-surprise-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = digest()
    return module.MarketResearchInitialClaimsSurpriseDigestSignal(
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
    cfg: object | None = None,
    generated_at: datetime = GENERATED_AT,
):
    module = digest()
    return module.build_market_research_initial_claims_surprise_digest(
        signals,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_initial_claims_surprise_digest_reduces_redacts_and_sorts() -> None:
    module = digest()

    summary = report(
        (
            claims_signal(
                "condition.initial-claims.ready",
                claims_market_key="us.initial-claims.ready",
                release_key="dol.initial-claims.ready",
                public_signal_reference="dol-initial-claims-public-release",
                forecast_claims=d("225000.000000"),
                actual_claims=d("245000.000000"),
                surprise_claims=d("20000.000000"),
                surprise_ratio=d("0.088889"),
                source_family_count=d("4.000000"),
                stale_source_ratio=d("0.050000"),
                confirmation_ratio=d("0.830000"),
                base_confidence=d("0.880000"),
            ),
            claims_signal(
                "condition.initial-claims.confirmation-gap",
                claims_market_key="us.initial-claims.confirmation-gap",
                release_key="dol.initial-claims.confirmation-gap",
                public_signal_reference="wallet://private/initial-claims-note",
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
                "condition.initial-claims.stale-soft",
                claims_market_key="us.initial-claims.stale-soft",
                release_key="dol.initial-claims.stale-soft",
                public_signal_reference=(
                    "https://labor.example/initial-claims?token=secret-123"
                ),
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
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, module.MarketResearchInitialClaimsSurpriseDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        module.DEFAULT_MARKET_RESEARCH_INITIAL_CLAIMS_SURPRISE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_initial_claims_surprise_digest"
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
    assert blocked.redacted_public_signal_reference == "sha256:a7cc8de0d43d"
    assert blocked.reason_codes == (
        "market_research_initial_claims_surprise_digest_stale_release",
        "market_research_initial_claims_surprise_digest_low_absolute_surprise",
        "market_research_initial_claims_surprise_digest_low_surprise_ratio",
        "market_research_initial_claims_surprise_digest_source_family_gap",
        "market_research_initial_claims_surprise_digest_stale_source_ratio",
        "market_research_initial_claims_surprise_digest_confirmation_gap",
    )

    watch = summary.rows[1]
    assert watch.digest_status == "watch"
    assert watch.confidence_decay_factor == d("0.100000")
    assert watch.final_confidence == d("0.660000")
    assert watch.redacted_public_signal_reference == "sha256:be03904a0f52"
    assert watch.reason_codes == (
        "market_research_initial_claims_surprise_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.880000")
    assert ready.redacted_public_signal_reference == "dol-initial-claims-public-release"
    assert ready.reason_codes == (
        "market_research_initial_claims_surprise_digest_ready",
    )

    assert summary.reason_code_counts == (
        module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_claims_surprise_digest_confirmation_gap",
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_claims_surprise_digest_stale_release",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
            reason_code=(
                "market_research_initial_claims_surprise_digest_"
                "low_absolute_surprise"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_claims_surprise_digest_low_surprise_ratio",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_claims_surprise_digest_source_family_gap",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_claims_surprise_digest_stale_source_ratio",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_claims_surprise_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        item.reason_code for item in summary.reason_code_counts
    )


def test_initial_claims_empty_digest_is_watch_and_decimal_only() -> None:
    module = digest()
    summary = report(())

    assert summary.digest_status == "watch"
    assert summary.recommended_next_step == (
        "watch_report_only_market_research_initial_claims_surprise_digest"
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
        module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
            reason_code="market_research_initial_claims_surprise_digest_no_inputs",
            count=d("0.000000"),
            signal_ratio=d("0.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_initial_claims_surprise_digest_no_inputs",
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


def test_initial_claims_validates_types_flags_freezing_and_consistency() -> None:
    module = digest()
    signal = claims_signal()
    summary = report((signal,))

    assert is_dataclass(module.MarketResearchInitialClaimsSurpriseDigestConfig)
    assert is_dataclass(module.MarketResearchInitialClaimsSurpriseDigestSignal)
    assert is_dataclass(module.MarketResearchInitialClaimsSurpriseDigestRow)
    assert is_dataclass(module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount)
    assert is_dataclass(module.MarketResearchInitialClaimsSurpriseDigestReport)
    cfg = config()
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        signal.condition_id = "changed"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):
        type("BadSignal", (module.MarketResearchInitialClaimsSurpriseDigestSignal,), {})

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(signal, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(signal, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(summary, readonly=False)
    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("initial-claims-v0"))
    with pytest.raises(ValueError, match="config_version"):
        config(config_version="unsupported-initial-claims-v0")
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
        report((), generated_at=datetime(2026, 7, 3, 16, 0, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="released_at"):
        claims_signal(released_at=_DatetimeSubclass(2026, 7, 3, tzinfo=UTC))
    with pytest.raises(ValueError, match="forecast_claims"):
        claims_signal(forecast_claims=Decimal("Infinity"))
    with pytest.raises(ValueError, match="actual_claims"):
        claims_signal(actual_claims=_DecimalSubclass("245000.000000"))
    with pytest.raises(ValueError, match="surprise_claims"):
        claims_signal(surprise_claims=d("-1.000000"))
    with pytest.raises(ValueError, match="condition_id"):
        claims_signal(condition_id=_StringSubclass("condition.subclass"))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="iterable"):
        module.build_market_research_initial_claims_surprise_digest(
            "not-a-list",
            config=config(),
            generated_at=GENERATED_AT,
        )  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="MarketResearchInitialClaimsSurpriseDigestSignal"):
        report((object(),))
    with pytest.raises(ValueError, match="config"):
        module.build_market_research_initial_claims_surprise_digest(
            (),
            config=object(),
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
                module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
                    reason_code=summary.reason_code_counts[0].reason_code,
                    count=d("2.000000"),
                    signal_ratio=d("1.000000"),
                ),
            ),
        )


def test_initial_claims_low_absolute_surprise_is_independent_reason() -> None:
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
    assert summary.blocked_signal_count == ZERO
    assert summary.low_absolute_surprise_signal_count == d("1.000000")
    assert summary.low_surprise_ratio_signal_count == ZERO
    assert summary.rows[0].confidence_decay_factor == d("0.100000")
    assert summary.rows[0].final_confidence == d("0.760000")
    assert summary.rows[0].reason_codes == (
        "market_research_initial_claims_surprise_digest_low_absolute_surprise",
    )


def test_initial_claims_sorting_is_deterministic_for_equal_status_and_market() -> None:
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


def test_initial_claims_payload_is_report_only_serialized_and_literal_safe() -> None:
    module = digest()
    summary = report((claims_signal(),))
    payload = module.market_research_initial_claims_surprise_digest_payload(summary)

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
    assert not any(isinstance(value, (Decimal, datetime, float)) for value in walk_values(payload))

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
        "network",
        "database",
        "wallet",
        "order",
        "token",
        "secret",
    ):
        assert token not in public


def test_initial_claims_signal_reference_is_redacted_before_storage() -> None:
    signal = claims_signal(
        public_signal_reference="https://labor.example/initial-claims?token=secret-123",
    )

    assert signal.public_signal_reference == "sha256:a7cc8de0d43d"
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


def test_initial_claims_rows_and_counts_are_frozen_dataclasses() -> None:
    module = digest()
    row = module.MarketResearchInitialClaimsSurpriseDigestRow(
        condition_id="condition.manual",
        claims_market_key="manual.initial-claims",
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
        reason_codes=("market_research_initial_claims_surprise_digest_ready",),
    )
    reason = module.MarketResearchInitialClaimsSurpriseDigestReasonCodeCount(
        reason_code="market_research_initial_claims_surprise_digest_ready",
        count=d("1.000000"),
        signal_ratio=d("1.000000"),
    )

    assert is_dataclass(row)
    assert is_dataclass(reason)
    with pytest.raises(FrozenInstanceError):
        row.digest_status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        reason.count = d("2.000000")  # type: ignore[misc]


def test_initial_claims_public_surface_excludes_io_and_mutation_domains() -> None:
    module_path = Path(
        "src/polymarket_alpha_lab/"
        "market_research_initial_claims_surprise_digest.py",
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
        "pathlib",
    }
    forbidden_literals = {
        "place_order",
        "cancel_order",
        "replace_order",
        "private_key",
        "wallet",
        "token",
        "secret",
        "exchange mutation",
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
            for module_name in modules:
                assert module_name.split(".")[0] not in forbidden_import_roots
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
