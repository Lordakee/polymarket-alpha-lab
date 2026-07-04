from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from hashlib import sha256
from pathlib import Path

import pytest

from polymarket_alpha_lab.market_research_ai_event_memory_digest import (
    DEFAULT_MARKET_RESEARCH_AI_EVENT_MEMORY_DIGEST_CONFIG_VERSION,
    MarketResearchAIEventMemoryDigestConfig,
    MarketResearchAIEventMemoryDigestInputRow,
    MarketResearchAIEventMemoryDigestReasonCodeCount,
    MarketResearchAIEventMemoryDigestReport,
    MarketResearchAIEventMemoryDigestRow,
    build_market_research_ai_event_memory_digest,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def redacted(value: str) -> str:
    return f"sha256:{sha256(value.encode()).hexdigest()[:12]}"


def config(**overrides: object) -> MarketResearchAIEventMemoryDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_AI_EVENT_MEMORY_DIGEST_CONFIG_VERSION,
        "fresh_source_max_age_seconds": d("21600.000000"),
        "min_source_count": d("2.000000"),
        "min_event_analog_count": d("2.000000"),
        "min_model_launch_catalyst_score": d("0.650000"),
        "min_product_policy_catalyst_score": d("0.600000"),
        "confidence_gap_threshold": d("0.250000"),
    }
    values.update(overrides)
    return MarketResearchAIEventMemoryDigestConfig(**values)


def ai_row(
    market_research_key: str = "research.alpha",
    *,
    ai_event_key: str = "ai.model.launch",
    ai_event_family: str = "model_launch",
    ai_event_reference: str = "public-model-card",
    event_observed_at: datetime | None = None,
    latest_source_observed_at: datetime | None = None,
    latest_analog_observed_at: datetime | None = None,
    source_count: Decimal = d("3.000000"),
    stale_source_count: Decimal = d("0.000000"),
    model_launch_catalyst_score: Decimal = d("0.800000"),
    product_policy_catalyst_score: Decimal = d("0.200000"),
    event_analog_count: Decimal = d("3.000000"),
    confidence_score: Decimal = d("0.760000"),
    confidence_gap_score: Decimal = d("0.100000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchAIEventMemoryDigestInputRow:
    return MarketResearchAIEventMemoryDigestInputRow(
        market_research_key=market_research_key,
        ai_event_key=ai_event_key,
        ai_event_family=ai_event_family,
        ai_event_reference=ai_event_reference,
        event_observed_at=event_observed_at or GENERATED_AT - timedelta(hours=1),
        latest_source_observed_at=latest_source_observed_at
        or GENERATED_AT - timedelta(hours=2),
        latest_analog_observed_at=latest_analog_observed_at
        or GENERATED_AT - timedelta(days=3),
        source_count=source_count,
        stale_source_count=stale_source_count,
        model_launch_catalyst_score=model_launch_catalyst_score,
        product_policy_catalyst_score=product_policy_catalyst_score,
        event_analog_count=event_analog_count,
        confidence_score=confidence_score,
        confidence_gap_score=confidence_gap_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[MarketResearchAIEventMemoryDigestInputRow, ...],
    *,
    cfg: MarketResearchAIEventMemoryDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchAIEventMemoryDigestReport:
    return build_market_research_ai_event_memory_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_ai_event_memory_digest_reduces_catalysts_freshness_analogs_and_gaps() -> None:
    summary = report(
        (
            ai_row(
                "research.ready",
                ai_event_key="openai.gpt.next",
                ai_event_family="model_launch",
                ai_event_reference="public-model-system-card",
                latest_source_observed_at=GENERATED_AT - timedelta(hours=1),
                event_analog_count=d("4.000000"),
                model_launch_catalyst_score=d("0.820000"),
                product_policy_catalyst_score=d("0.220000"),
                confidence_gap_score=d("0.080000"),
            ),
            ai_row(
                "research.watch",
                ai_event_key="anthropic.policy.change",
                ai_event_family="product_policy",
                ai_event_reference="https://vendor.example/private?token=ai-secret",
                event_observed_at=GENERATED_AT - timedelta(hours=8),
                latest_source_observed_at=GENERATED_AT - timedelta(hours=9),
                latest_analog_observed_at=GENERATED_AT - timedelta(days=30),
                source_count=d("1.000000"),
                stale_source_count=d("1.000000"),
                model_launch_catalyst_score=d("0.300000"),
                product_policy_catalyst_score=d("0.720000"),
                event_analog_count=d("1.000000"),
                confidence_score=d("0.520000"),
                confidence_gap_score=d("0.300000"),
            ),
            ai_row(
                "research.blocked",
                ai_event_key="xai.unknown.release",
                ai_event_family="model_launch",
                ai_event_reference="wallet://private/ai-feed",
                latest_source_observed_at=None,
                latest_analog_observed_at=None,
                source_count=d("0.000000"),
                stale_source_count=d("0.000000"),
                model_launch_catalyst_score=d("0.580000"),
                product_policy_catalyst_score=d("0.140000"),
                event_analog_count=d("0.000000"),
                confidence_score=d("0.200000"),
                confidence_gap_score=d("0.450000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert isinstance(summary, MarketResearchAIEventMemoryDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == DEFAULT_MARKET_RESEARCH_AI_EVENT_MEMORY_DIGEST_CONFIG_VERSION
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ai_event_memory_digest"
    )
    assert summary.ai_event_count == d("3.000000")
    assert summary.ready_event_count == d("1.000000")
    assert summary.watch_event_count == d("1.000000")
    assert summary.blocked_event_count == d("1.000000")
    assert summary.model_launch_catalyst_count == d("1.000000")
    assert summary.product_policy_catalyst_count == d("1.000000")
    assert summary.stale_source_event_count == d("1.000000")
    assert summary.missing_source_event_count == d("1.000000")
    assert summary.thin_source_event_count == d("2.000000")
    assert summary.missing_analog_event_count == d("1.000000")
    assert summary.thin_analog_event_count == d("2.000000")
    assert summary.confidence_gap_event_count == d("2.000000")
    assert summary.source_count == d("4.000000")
    assert summary.stale_source_count == d("1.000000")
    assert summary.event_analog_count == d("5.000000")
    assert summary.source_freshness_ratio == d("0.750000")
    assert summary.event_analog_coverage_ratio == d("0.666667")
    assert summary.average_confidence_score == d("0.493333")
    assert summary.average_confidence_gap_score == d("0.276667")
    assert summary.max_source_age_seconds == d("32400.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple(row.ai_event_key for row in summary.rows) == (
        "xai.unknown.release",
        "anthropic.policy.change",
        "openai.gpt.next",
    )

    blocked = summary.rows[0]
    assert blocked.memory_status == "blocked"
    assert blocked.source_age_seconds is None
    assert blocked.analog_age_seconds is None
    assert blocked.redacted_ai_event_reference == redacted("wallet://private/ai-feed")
    assert blocked.reason_codes == (
        "market_research_ai_event_memory_digest_confidence_gap",
        "market_research_ai_event_memory_digest_missing_event_analogs",
        "market_research_ai_event_memory_digest_missing_sources",
        "market_research_ai_event_memory_digest_model_launch_catalyst_gap",
        "market_research_ai_event_memory_digest_thin_event_analogs",
        "market_research_ai_event_memory_digest_thin_sources",
    )

    watch = summary.rows[1]
    assert watch.memory_status == "watch"
    assert watch.source_age_seconds == d("32400.000000")
    assert watch.analog_age_seconds == d("2592000.000000")
    assert watch.redacted_ai_event_reference == redacted(
        "https://vendor.example/private?token=ai-secret",
    )
    assert watch.reason_codes == (
        "market_research_ai_event_memory_digest_confidence_gap",
        "market_research_ai_event_memory_digest_product_policy_catalyst",
        "market_research_ai_event_memory_digest_stale_sources",
        "market_research_ai_event_memory_digest_thin_event_analogs",
        "market_research_ai_event_memory_digest_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.memory_status == "ready"
    assert ready.source_age_seconds == d("3600.000000")
    assert ready.analog_age_seconds == d("259200.000000")
    assert ready.redacted_ai_event_reference == "public-model-system-card"
    assert ready.reason_codes == (
        "market_research_ai_event_memory_digest_model_launch_catalyst",
        "market_research_ai_event_memory_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_confidence_gap",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_missing_event_analogs",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_missing_sources",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_model_launch_catalyst",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_model_launch_catalyst_gap",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_product_policy_catalyst",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_ready",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_stale_sources",
            count=d("1.000000"),
            event_ratio=d("0.333333"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_thin_event_analogs",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_thin_sources",
            count=d("2.000000"),
            event_ratio=d("0.666667"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "ai-secret",
        "vendor.example",
        "wallet://",
        "private/ai-feed",
        "auth",
        "broker",
        "signing",
        "submit",
        "cancel",
        "account",
        "advice",
    ):
        assert token not in public


def test_ai_event_memory_digest_empty_inputs_returns_report_only_blocked_digest() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ai_event_memory_digest"
    )
    assert summary.ai_event_count == d("0.000000")
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_ai_event_memory_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchAIEventMemoryDigestReasonCodeCount(
            reason_code="market_research_ai_event_memory_digest_no_inputs",
            count=d("1.000000"),
            event_ratio=d("0.000000"),
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_ai_event_memory_digest_validates_decimal_datetime_flags_and_types() -> None:
    with pytest.raises(TypeError, match="Decimal"):
        ai_row(source_count=1)  # type: ignore[arg-type]

    with pytest.raises(TypeError, match="datetime"):
        ai_row(event_observed_at="2026-07-02T11:00:00Z")  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="UTC-aware"):
        ai_row(event_observed_at=datetime(2026, 7, 2, 11, 0))

    with pytest.raises(ValueError, match="whole second"):
        ai_row(event_observed_at=datetime(2026, 7, 2, 11, 0, 0, 1, tzinfo=UTC))

    with pytest.raises(ValueError, match="paper_only"):
        ai_row(paper_only=False)

    with pytest.raises(ValueError, match="report_only"):
        ai_row(report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        ai_row(readonly=False)

    with pytest.raises(ValueError, match="canonical"):
        ai_row(ai_event_key=" Bad Key ")

    with pytest.raises(ValueError, match="unsafe"):
        ai_row(ai_event_reference="auth-token-publication")

    with pytest.raises(ValueError, match="stale_source_count"):
        ai_row(source_count=d("1.000000"), stale_source_count=d("2.000000"))

    with pytest.raises(TypeError, match="exactly"):
        MarketResearchAIEventMemoryDigestInputRow(
            market_research_key=_StringSubclass("research.alpha"),
            ai_event_key="ai.model.launch",
            ai_event_family="model_launch",
            ai_event_reference="public-model-card",
            event_observed_at=GENERATED_AT,
            latest_source_observed_at=GENERATED_AT,
            latest_analog_observed_at=GENERATED_AT,
            source_count=d("1.000000"),
            stale_source_count=d("0.000000"),
            model_launch_catalyst_score=d("0.800000"),
            product_policy_catalyst_score=d("0.100000"),
            event_analog_count=d("2.000000"),
            confidence_score=d("0.700000"),
            confidence_gap_score=d("0.100000"),
        )

    with pytest.raises(TypeError, match="exactly"):
        ai_row(event_observed_at=_DateTimeSubclass(2026, 7, 2, 11, 0, tzinfo=UTC))

    with pytest.raises(TypeError, match="exactly"):
        ai_row(source_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="unit interval"):
        ai_row(confidence_score=d("1.000001"))

    with pytest.raises(ValueError, match="nonnegative"):
        ai_row(source_count=d("-1.000000"))

    frozen = ai_row()
    with pytest.raises(FrozenInstanceError):
        frozen.source_count = d("99.000000")  # type: ignore[misc]

    summary = report((ai_row(event_observed_at=GENERATED_AT - timedelta(hours=1)),))
    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "ready"  # type: ignore[misc]

    assert replace(frozen, source_count=d("4.000000")).source_count == d("4.000000")


def test_ai_event_memory_digest_rejects_invalid_constructed_reports_and_reasons() -> None:
    good = report((ai_row(),))
    good_row = good.rows[0]

    with pytest.raises(ValueError, match="memory_status"):
        replace(good_row, memory_status="blocked")

    with pytest.raises(ValueError, match="reason_code"):
        replace(good_row, reason_codes=("unknown_reason",))

    with pytest.raises(ValueError, match="duplicate"):
        replace(
            good_row,
            reason_codes=(
                "market_research_ai_event_memory_digest_ready",
                "market_research_ai_event_memory_digest_ready",
            ),
        )

    with pytest.raises(ValueError, match="recommended_next_step"):
        replace(good, recommended_next_step="submit_order")

    with pytest.raises(ValueError, match="reason_codes"):
        replace(good, reason_codes=("market_research_ai_event_memory_digest_ready", "bad"))

    with pytest.raises(ValueError, match="rows"):
        replace(good, rows=(object(),))  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(good, reason_code_counts=(object(),))  # type: ignore[arg-type]


def test_ai_event_memory_digest_module_is_report_only_and_has_no_io_or_trading_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "market_research_ai_event_memory_digest.py"
    )
    source = module_path.read_text(encoding="utf-8")
    tree = ast.parse(source)

    forbidden_import_roots = {
        "builtins",
        "io",
        "json",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "sys",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "delete",
        "cursor",
        "execute",
        "open",
        "post",
        "put",
        "read_text",
        "send",
        "submit",
        "write_text",
    }
    forbidden_terms = (
        "wallet",
        "broker",
        "signing",
        "order",
        "cancel",
        "account",
        "advice",
    )

    imported_roots: set[str] = set()
    calls: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".", 1)[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".", 1)[0])
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                calls.add(func.id)
            elif isinstance(func, ast.Attribute):
                calls.add(func.attr)

    assert imported_roots.isdisjoint(forbidden_import_roots)
    assert calls.isdisjoint(forbidden_calls)
    assert not any(term in source.lower() for term in forbidden_terms)

    for cls in (
        MarketResearchAIEventMemoryDigestConfig,
        MarketResearchAIEventMemoryDigestInputRow,
        MarketResearchAIEventMemoryDigestRow,
        MarketResearchAIEventMemoryDigestReasonCodeCount,
        MarketResearchAIEventMemoryDigestReport,
    ):
        assert is_dataclass(cls)
        assert cls.__dataclass_params__.frozen is True
