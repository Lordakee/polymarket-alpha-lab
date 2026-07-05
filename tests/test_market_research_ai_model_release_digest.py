from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_ai_model_release_digest import (
    DEFAULT_MARKET_RESEARCH_AI_MODEL_RELEASE_DIGEST_CONFIG_VERSION,
    MarketResearchAiModelReleaseDigestConfig,
    MarketResearchAiModelReleaseDigestInputRow,
    MarketResearchAiModelReleaseDigestReasonCodeCount,
    MarketResearchAiModelReleaseDigestReport,
    MarketResearchAiModelReleaseDigestRow,
    build_market_research_ai_model_release_digest,
    market_research_ai_model_release_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_ai_model_release_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchAiModelReleaseDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_AI_MODEL_RELEASE_DIGEST_CONFIG_VERSION
        ),
        "fresh_release_max_age_seconds": d("86400.000000"),
        "high_impact_capability_threshold": d("0.200000"),
        "min_public_source_count": d("2"),
        "max_review_lag_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return MarketResearchAiModelReleaseDigestConfig(**values)


def input_row(
    research_key: str = "research.ai.model.frontier",
    *,
    condition_id: str = "condition_ai_model_frontier",
    model_family: str = "frontier_reasoning",
    public_release_reference: str = "public-model-release-note",
    released_at: datetime | None = None,
    reviewed_at: object = _UNSET,
    public_source_count: Decimal = d("3"),
    capability_delta: Decimal = d("0.120000"),
    benchmark_delta: Decimal = d("0.180000"),
    probability_before: Decimal = d("0.420000"),
    probability_after: Decimal = d("0.500000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchAiModelReleaseDigestInputRow:
    return MarketResearchAiModelReleaseDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        model_family=model_family,
        public_release_reference=public_release_reference,
        released_at=released_at or GENERATED_AT - timedelta(hours=1),
        reviewed_at=(
            GENERATED_AT - timedelta(minutes=30)
            if reviewed_at is _UNSET
            else reviewed_at
        ),
        public_source_count=public_source_count,
        capability_delta=capability_delta,
        benchmark_delta=benchmark_delta,
        probability_before=probability_before,
        probability_after=probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchAiModelReleaseDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchAiModelReleaseDigestReport:
    return build_market_research_ai_model_release_digest(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if isinstance(item, Decimal) or item is None:
            continue
        if field.name.endswith("_count") or field.name.endswith("_ratio"):
            assert type(item) is Decimal
        if field.name.endswith("_seconds") or field.name.endswith("_delta"):
            assert type(item) is Decimal


def test_ai_model_release_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.ai.model.small",
                condition_id="condition_ai_model_small",
                model_family="small_open_model",
                public_release_reference="https://vendor.example/release?token=hidden",
                released_at=GENERATED_AT - timedelta(hours=30),
                reviewed_at=GENERATED_AT - timedelta(hours=4),
                public_source_count=d("1"),
                capability_delta=d("0.050000"),
                benchmark_delta=d("0.070000"),
                probability_before=d("0.300000"),
                probability_after=d("0.330000"),
            ),
            input_row(
                "research.ai.model.video",
                condition_id="condition_ai_model_video",
                model_family="video_generation",
                public_release_reference="private-model-brief",
                released_at=GENERATED_AT - timedelta(hours=3),
                reviewed_at=None,
                public_source_count=d("2"),
                capability_delta=d("0.280000"),
                benchmark_delta=d("0.310000"),
                probability_before=d("0.460000"),
                probability_after=d("0.610000"),
            ),
            input_row(
                "research.ai.model.frontier",
                condition_id="condition_ai_model_frontier",
                model_family="frontier_reasoning",
                public_release_reference="public-model-release-note",
                released_at=GENERATED_AT - timedelta(minutes=45),
                reviewed_at=GENERATED_AT - timedelta(minutes=15),
                public_source_count=d("3"),
                capability_delta=d("0.120000"),
                benchmark_delta=d("0.180000"),
                probability_before=d("0.420000"),
                probability_after=d("0.500000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_AI_MODEL_RELEASE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ai_model_release_digest"
    )
    assert summary.release_count == d("3.000000")
    assert summary.ready_release_count == d("1.000000")
    assert summary.watch_release_count == d("1.000000")
    assert summary.blocked_release_count == d("1.000000")
    assert summary.high_impact_release_count == d("1.000000")
    assert summary.stale_release_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_review_count == d("1.000000")
    assert summary.slow_review_count == d("1.000000")
    assert summary.probability_repricing_count == d("1.000000")
    assert summary.average_capability_delta == d("0.150000")
    assert summary.max_release_age_seconds == d("108000.000000")
    assert summary.average_public_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.model_family, row.research_key) for row in summary.rows) == (
        ("video_generation", "research.ai.model.video"),
        ("small_open_model", "research.ai.model.small"),
        ("frontier_reasoning", "research.ai.model.frontier"),
    )

    video = summary.rows[0]
    assert video.release_status == "blocked"
    assert video.release_age_seconds == d("10800.000000")
    assert video.review_lag_seconds is None
    assert video.capability_delta_abs == d("0.280000")
    assert video.probability_delta == d("0.150000")
    assert video.redacted_release_reference == "sha256:6c6395e04b31"
    assert video.reason_codes == (
        "market_research_ai_model_release_digest_high_impact_release",
        "market_research_ai_model_release_digest_missing_review",
        "market_research_ai_model_release_digest_probability_repricing",
    )

    small = summary.rows[1]
    assert small.release_status == "watch"
    assert small.release_age_seconds == d("108000.000000")
    assert small.review_lag_seconds == d("93600.000000")
    assert small.redacted_release_reference == "sha256:354eb0bc6ec1"
    assert small.reason_codes == (
        "market_research_ai_model_release_digest_slow_review",
        "market_research_ai_model_release_digest_stale_release",
        "market_research_ai_model_release_digest_thin_sources",
    )

    frontier = summary.rows[2]
    assert frontier.release_status == "ready"
    assert frontier.release_age_seconds == d("2700.000000")
    assert frontier.review_lag_seconds == d("1800.000000")
    assert frontier.redacted_release_reference == "public-model-release-note"
    assert frontier.reason_codes == (
        "market_research_ai_model_release_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code="market_research_ai_model_release_digest_stale_release",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code=(
                "market_research_ai_model_release_digest_high_impact_release"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code="market_research_ai_model_release_digest_missing_review",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code=(
                "market_research_ai_model_release_digest_probability_repricing"
            ),
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code="market_research_ai_model_release_digest_slow_review",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code="market_research_ai_model_release_digest_thin_sources",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code="market_research_ai_model_release_digest_ready",
            count=d("1.000000"),
            release_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for token in (
        "hidden",
        "vendor.example",
        "https://",
        "private-model-brief",
        "token",
        "private",
    ):
        assert token not in public


def test_empty_ai_model_release_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_ai_model_release_digest"
    )
    assert summary.release_count == ZERO
    assert summary.ready_release_count == ZERO
    assert summary.watch_release_count == ZERO
    assert summary.blocked_release_count == ZERO
    assert summary.average_capability_delta == ZERO
    assert summary.max_release_age_seconds == ZERO
    assert summary.average_public_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchAiModelReleaseDigestReasonCodeCount(
            reason_code="market_research_ai_model_release_digest_no_inputs",
            count=d("1.000000"),
            release_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_ai_model_release_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_ai_model_release_digest_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = market_research_ai_model_release_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["release_count"] == "1.000000"
    assert payload["average_capability_delta"] == "0.120000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_release_reference':" not in repr(payload)
    assert "private" not in repr(payload).lower()


def test_ai_model_release_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchAiModelReleaseDigestConfig)
    assert is_dataclass(MarketResearchAiModelReleaseDigestInputRow)
    assert is_dataclass(MarketResearchAiModelReleaseDigestRow)
    assert is_dataclass(MarketResearchAiModelReleaseDigestReasonCodeCount)
    assert is_dataclass(MarketResearchAiModelReleaseDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("ai-model-release-v0"))
    with pytest.raises(ValueError, match="fresh_release_max_age_seconds"):
        config(fresh_release_max_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="high_impact_capability_threshold"):
        config(high_impact_capability_threshold=Decimal("NaN"))
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="max_review_lag_seconds"):
        config(max_review_lag_seconds=_DecimalSubclass("7200"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="broker_feed")
    with pytest.raises(ValueError, match="released_at"):
        input_row(released_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="reviewed_at"):
        input_row(reviewed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="public_source_count"):
        input_row(public_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="capability_delta"):
        input_row(capability_delta=Decimal("Infinity"))
    with pytest.raises(ValueError, match="benchmark_delta"):
        input_row(benchmark_delta=_DecimalSubclass("0.200000"))
    with pytest.raises(ValueError, match="probability_before"):
        input_row(probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="probability_after"):
        input_row(probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_ai_model_release_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_ai_model_release_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]
    risky_summary = report(
        (
            input_row(
                "research.ai.model.video",
                condition_id="condition_ai_model_video",
                model_family="video_generation",
                reviewed_at=None,
                capability_delta=d("0.280000"),
                benchmark_delta=d("0.310000"),
                probability_before=d("0.460000"),
                probability_after=d("0.610000"),
            ),
        ),
    )

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_ai_model_release_digest_ready",
                "market_research_ai_model_release_digest_high_impact_release",
            ),
        )
    with pytest.raises(ValueError, match="release_status"):
        replace(ready, release_status="blocked")
    with pytest.raises(ValueError, match="capability_delta_abs"):
        replace(ready, capability_delta_abs=d("9.999999"))
    with pytest.raises(ValueError, match="benchmark_delta_abs"):
        replace(ready, benchmark_delta_abs=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_release_reference"):
        replace(ready, redacted_release_reference="https://host?token=hidden")

    with pytest.raises(ValueError, match="ready_release_count"):
        replace(report((input_row(),)), ready_release_count=ZERO)
    with pytest.raises(ValueError, match="high_impact_release_count"):
        replace(risky_summary, high_impact_release_count=ZERO)
    with pytest.raises(ValueError, match="average_capability_delta"):
        replace(risky_summary, average_capability_delta=ZERO)
    with pytest.raises(ValueError, match="digest_status"):
        replace(
            risky_summary,
            digest_status="ready",
            recommended_next_step=(
                "allow_report_only_market_research_ai_model_release_digest"
            ),
        )
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.ai.model.z", model_family="zeta_model"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_durable_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
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
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "signing",
        "advice",
        "market_slug",
        "question",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
        "database",
        "durable",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for token in forbidden_fragments:
        assert token not in lowered
