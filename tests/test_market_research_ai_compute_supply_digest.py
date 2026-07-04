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

from polymarket_alpha_lab.market_research_ai_compute_supply_digest import (
    DEFAULT_MARKET_RESEARCH_AI_COMPUTE_SUPPLY_DIGEST_CONFIG_VERSION,
    MarketResearchAiComputeSupplyDigestConfig,
    MarketResearchAiComputeSupplyDigestInputRow,
    MarketResearchAiComputeSupplyDigestReasonCodeCount,
    MarketResearchAiComputeSupplyDigestReport,
    build_market_research_ai_compute_supply_digest,
    market_research_ai_compute_supply_digest_payload,
)


ZERO = Decimal("0.000000")
GENERATED_AT = datetime(2026, 7, 4, 14, 30, tzinfo=UTC)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_ai_compute_supply_digest.py",
)
_UNSET = object()


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchAiComputeSupplyDigestConfig:
    values = {
        "config_version": DEFAULT_MARKET_RESEARCH_AI_COMPUTE_SUPPLY_DIGEST_CONFIG_VERSION,
        "fresh_supply_max_age_seconds": d("86400.000000"),
        "min_public_source_count": d("2"),
        "min_ready_supply_score": d("0.650000"),
        "min_watch_supply_score": d("0.350000"),
        "max_demand_pressure_score": d("0.700000"),
        "max_supply_disruption_score": d("0.500000"),
        "max_provider_concentration_score": d("0.650000"),
        "max_review_lag_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return MarketResearchAiComputeSupplyDigestConfig(**values)


def input_row(
    research_key: str = "research.ai.compute.frontier",
    *,
    condition_id: str = "condition_ai_compute_frontier",
    compute_segment: str = "frontier_accelerators",
    public_supply_reference: str = "public-compute-supply-memo",
    supply_observed_at: datetime | None = None,
    reviewed_at: datetime | None | object = _UNSET,
    public_source_count: Decimal = d("3"),
    available_supply_score: Decimal = d("0.800000"),
    demand_pressure_score: Decimal = d("0.300000"),
    supply_disruption_score: Decimal = d("0.100000"),
    provider_concentration_score: Decimal = d("0.400000"),
    market_probability_before: Decimal = d("0.420000"),
    market_probability_after: Decimal = d("0.500000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchAiComputeSupplyDigestInputRow:
    return MarketResearchAiComputeSupplyDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        compute_segment=compute_segment,
        public_supply_reference=public_supply_reference,
        supply_observed_at=supply_observed_at or GENERATED_AT - timedelta(hours=1),
        reviewed_at=(
            GENERATED_AT - timedelta(minutes=30)
            if reviewed_at is _UNSET
            else reviewed_at
        ),
        public_source_count=public_source_count,
        available_supply_score=available_supply_score,
        demand_pressure_score=demand_pressure_score,
        supply_disruption_score=supply_disruption_score,
        provider_concentration_score=provider_concentration_score,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchAiComputeSupplyDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchAiComputeSupplyDigestReport:
    return build_market_research_ai_compute_supply_digest(
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
        if field.name.endswith("_seconds") or field.name.endswith("_score"):
            assert type(item) is Decimal
        if field.name.endswith("_change"):
            assert type(item) is Decimal


def test_ai_compute_supply_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.ai.compute.legacy",
                condition_id="condition_ai_compute_legacy",
                compute_segment="legacy_accelerators",
                public_supply_reference="https://vendor.example/supply?credential=hidden",
                supply_observed_at=GENERATED_AT - timedelta(hours=30),
                reviewed_at=GENERATED_AT - timedelta(hours=4),
                public_source_count=d("1"),
                available_supply_score=d("0.500000"),
                demand_pressure_score=d("0.600000"),
                supply_disruption_score=d("0.200000"),
                provider_concentration_score=d("0.400000"),
                market_probability_before=d("0.300000"),
                market_probability_after=d("0.330000"),
            ),
            input_row(
                "research.ai.compute.cluster",
                condition_id="condition_ai_compute_cluster",
                compute_segment="frontier_cluster",
                public_supply_reference="confidential-compute-brief",
                supply_observed_at=GENERATED_AT - timedelta(hours=3),
                reviewed_at=None,
                public_source_count=d("2"),
                available_supply_score=d("0.300000"),
                demand_pressure_score=d("0.800000"),
                supply_disruption_score=d("0.600000"),
                provider_concentration_score=d("0.700000"),
                market_probability_before=d("0.460000"),
                market_probability_after=d("0.610000"),
            ),
            input_row(
                "research.ai.compute.frontier",
                condition_id="condition_ai_compute_frontier",
                compute_segment="frontier_accelerators",
                public_supply_reference="public-compute-supply-memo",
                supply_observed_at=GENERATED_AT - timedelta(minutes=45),
                reviewed_at=GENERATED_AT - timedelta(minutes=15),
                public_source_count=d("3"),
                available_supply_score=d("0.800000"),
                demand_pressure_score=d("0.300000"),
                supply_disruption_score=d("0.100000"),
                provider_concentration_score=d("0.400000"),
                market_probability_before=d("0.420000"),
                market_probability_after=d("0.500000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_AI_COMPUTE_SUPPLY_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.next_step == "block_report_only_market_research_ai_compute_supply_digest"
    assert summary.supply_count == d("3.000000")
    assert summary.ready_supply_count == d("1.000000")
    assert summary.watch_supply_count == d("1.000000")
    assert summary.blocked_supply_count == d("1.000000")
    assert summary.constrained_supply_count == d("1.000000")
    assert summary.tight_supply_count == d("1.000000")
    assert summary.high_demand_pressure_count == d("1.000000")
    assert summary.supply_disruption_count == d("1.000000")
    assert summary.provider_concentration_count == d("1.000000")
    assert summary.stale_supply_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.missing_review_count == d("1.000000")
    assert summary.slow_review_count == d("1.000000")
    assert summary.average_available_supply_score == d("0.533333")
    assert summary.max_supply_age_seconds == d("108000.000000")
    assert summary.average_public_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.supply_status, row.compute_segment) for row in summary.rows) == (
        ("blocked", "frontier_cluster"),
        ("watch", "legacy_accelerators"),
        ("ready", "frontier_accelerators"),
    )

    blocked = summary.rows[0]
    assert blocked.supply_age_seconds == d("10800.000000")
    assert blocked.review_lag_seconds is None
    assert blocked.probability_change == d("0.150000")
    assert blocked.redacted_supply_reference == "sha256:418d6df069c6"
    assert blocked.reason_codes == (
        "market_research_ai_compute_supply_digest_constrained_supply",
        "market_research_ai_compute_supply_digest_high_demand_pressure",
        "market_research_ai_compute_supply_digest_missing_review",
        "market_research_ai_compute_supply_digest_probability_shift",
        "market_research_ai_compute_supply_digest_provider_concentration",
        "market_research_ai_compute_supply_digest_supply_disruption",
    )

    watch = summary.rows[1]
    assert watch.supply_age_seconds == d("108000.000000")
    assert watch.review_lag_seconds == d("93600.000000")
    assert watch.redacted_supply_reference == "sha256:49bab7d5c151"
    assert watch.reason_codes == (
        "market_research_ai_compute_supply_digest_slow_review",
        "market_research_ai_compute_supply_digest_stale_supply",
        "market_research_ai_compute_supply_digest_thin_sources",
        "market_research_ai_compute_supply_digest_tight_supply",
    )

    ready = summary.rows[2]
    assert ready.supply_status == "ready"
    assert ready.supply_age_seconds == d("2700.000000")
    assert ready.review_lag_seconds == d("1800.000000")
    assert ready.redacted_supply_reference == "public-compute-supply-memo"
    assert ready.reason_codes == (
        "market_research_ai_compute_supply_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_constrained_supply",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_missing_review",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_probability_shift",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_high_demand_pressure",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_supply_disruption",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code=(
                "market_research_ai_compute_supply_digest_provider_concentration"
            ),
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_tight_supply",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_slow_review",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_stale_supply",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_thin_sources",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_ready",
            count=d("1.000000"),
            supply_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "hidden",
        "vendor.example",
        "https://",
        "confidential-compute-brief",
        "credential",
    ):
        assert value not in public


def test_empty_ai_compute_supply_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.next_step == "block_report_only_market_research_ai_compute_supply_digest"
    assert summary.supply_count == ZERO
    assert summary.ready_supply_count == ZERO
    assert summary.watch_supply_count == ZERO
    assert summary.blocked_supply_count == ZERO
    assert summary.average_available_supply_score == ZERO
    assert summary.max_supply_age_seconds == ZERO
    assert summary.average_public_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchAiComputeSupplyDigestReasonCodeCount(
            reason_code="market_research_ai_compute_supply_digest_no_inputs",
            count=d("1.000000"),
            supply_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_ai_compute_supply_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_ai_compute_supply_digest_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = market_research_ai_compute_supply_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["supply_count"] == "1.000000"
    assert payload["average_available_supply_score"] == "0.800000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(type(value) in (float, int) for value in walk_values(payload))
    assert "'public_supply_reference':" not in repr(payload)
    assert "confidential" not in repr(payload).lower()


def test_ai_compute_supply_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchAiComputeSupplyDigestConfig)
    assert is_dataclass(MarketResearchAiComputeSupplyDigestInputRow)

    api = importlib.import_module(
        "polymarket_alpha_lab.market_research_ai_compute_supply_digest",
    )
    assert is_dataclass(api.MarketResearchAiComputeSupplyDigestRow)
    assert is_dataclass(api.MarketResearchAiComputeSupplyDigestReasonCodeCount)
    assert is_dataclass(api.MarketResearchAiComputeSupplyDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("ai-compute-supply-v0"))
    with pytest.raises(ValueError, match="fresh_supply_max_age_seconds"):
        config(fresh_supply_max_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="min_ready_supply_score"):
        config(min_ready_supply_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="min_watch_supply_score"):
        config(min_watch_supply_score=d("-0.000001"))
    with pytest.raises(ValueError, match="max_demand_pressure_score"):
        config(max_demand_pressure_score=d("1.000001"))
    with pytest.raises(ValueError, match="max_supply_disruption_score"):
        config(max_supply_disruption_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="max_provider_concentration_score"):
        config(max_provider_concentration_score=d("-0.000001"))
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="live_surface")
    with pytest.raises(ValueError, match="supply_observed_at"):
        input_row(supply_observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="reviewed_at"):
        input_row(reviewed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="public_source_count"):
        input_row(public_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="available_supply_score"):
        input_row(available_supply_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="demand_pressure_score"):
        input_row(demand_pressure_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="market_probability_before"):
        input_row(market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="market_probability_after"):
        input_row(market_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_ai_compute_supply_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_ai_compute_supply_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_ai_compute_supply_digest_ready",
                "market_research_ai_compute_supply_digest_tight_supply",
            ),
        )
    with pytest.raises(ValueError, match="supply_status"):
        replace(ready, supply_status="blocked")
    with pytest.raises(ValueError, match="probability_change"):
        replace(ready, probability_change=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_supply_reference"):
        replace(ready, redacted_supply_reference="https://host?credential=hidden")

    with pytest.raises(ValueError, match="ready_supply_count"):
        replace(report((input_row(),)), ready_supply_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.ai.compute.z", compute_segment="zeta_compute"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_or_execution_surfaces() -> None:
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
    for value in forbidden_fragments:
        assert value not in lowered
