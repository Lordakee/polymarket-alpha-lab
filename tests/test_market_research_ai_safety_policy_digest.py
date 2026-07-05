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

from polymarket_alpha_lab.market_research_ai_safety_policy_digest import (
    DEFAULT_MARKET_RESEARCH_AI_SAFETY_POLICY_DIGEST_CONFIG_VERSION,
    MarketResearchAiSafetyPolicyDigestConfig,
    MarketResearchAiSafetyPolicyDigestInputRow,
    MarketResearchAiSafetyPolicyDigestReasonCodeCount,
    MarketResearchAiSafetyPolicyDigestReport,
    MarketResearchAiSafetyPolicyDigestRow,
    build_market_research_ai_safety_policy_digest,
    market_research_ai_safety_policy_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_ai_safety_policy_digest.py",
)


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchAiSafetyPolicyDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_AI_SAFETY_POLICY_DIGEST_CONFIG_VERSION
        ),
        "fresh_policy_max_age_seconds": d("86400.000000"),
        "min_public_source_count": d("2"),
        "min_cross_source_agreement": d("0.600000"),
        "materiality_watch_threshold": d("0.150000"),
        "materiality_block_threshold": d("0.350000"),
        "max_review_lag_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return MarketResearchAiSafetyPolicyDigestConfig(**values)


def input_row(
    research_key: str = "research.ai.safety.frontier",
    *,
    condition_id: str = "condition_ai_safety_frontier",
    policy_area: str = "frontier_model_rules",
    public_policy_reference: str = "public-policy-memo",
    policy_observed_at: datetime | None = None,
    reviewed_at: object = _UNSET,
    public_source_count: Decimal = d("3"),
    cross_source_agreement: Decimal = d("0.800000"),
    impact_materiality_score: Decimal = d("0.120000"),
    market_probability_before: Decimal = d("0.420000"),
    market_probability_after: Decimal = d("0.500000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchAiSafetyPolicyDigestInputRow:
    return MarketResearchAiSafetyPolicyDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        policy_area=policy_area,
        public_policy_reference=public_policy_reference,
        policy_observed_at=policy_observed_at or GENERATED_AT - timedelta(hours=1),
        reviewed_at=(
            GENERATED_AT - timedelta(minutes=30)
            if reviewed_at is _UNSET
            else reviewed_at
        ),
        public_source_count=public_source_count,
        cross_source_agreement=cross_source_agreement,
        impact_materiality_score=impact_materiality_score,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchAiSafetyPolicyDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchAiSafetyPolicyDigestReport:
    return build_market_research_ai_safety_policy_digest(
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
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if (
            field.name.endswith(
                (
                    "_agreement",
                    "_change",
                    "_count",
                    "_ratio",
                    "_score",
                    "_seconds",
                ),
            )
            or "probability" in field.name
        ):
            assert type(item) is Decimal


def test_ai_safety_policy_digest_reduces_rows_redacts_refs_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.ai.safety.archived",
                condition_id="condition_ai_safety_archived",
                policy_area="archived_rules",
                public_policy_reference="https://vendor.example/policy?credential=hidden",
                policy_observed_at=GENERATED_AT - timedelta(hours=30),
                reviewed_at=GENERATED_AT - timedelta(hours=4),
                public_source_count=d("1"),
                cross_source_agreement=d("0.500000"),
                impact_materiality_score=d("0.200000"),
                market_probability_before=d("0.300000"),
                market_probability_after=d("0.330000"),
            ),
            input_row(
                "research.ai.safety.eval",
                condition_id="condition_ai_safety_eval",
                policy_area="evaluation_rules",
                public_policy_reference="confidential-policy-brief",
                policy_observed_at=GENERATED_AT - timedelta(hours=3),
                reviewed_at=None,
                public_source_count=d("2"),
                cross_source_agreement=d("0.700000"),
                impact_materiality_score=d("0.420000"),
                market_probability_before=d("0.460000"),
                market_probability_after=d("0.610000"),
            ),
            input_row(
                "research.ai.safety.frontier",
                condition_id="condition_ai_safety_frontier",
                policy_area="frontier_model_rules",
                public_policy_reference="public-policy-memo",
                policy_observed_at=GENERATED_AT - timedelta(minutes=45),
                reviewed_at=GENERATED_AT - timedelta(minutes=15),
                public_source_count=d("3"),
                cross_source_agreement=d("0.800000"),
                impact_materiality_score=d("0.120000"),
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
        DEFAULT_MARKET_RESEARCH_AI_SAFETY_POLICY_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.next_step == "block_report_only_market_research_ai_safety_policy_digest"
    assert summary.policy_count == d("3.000000")
    assert summary.ready_policy_count == d("1.000000")
    assert summary.watch_policy_count == d("1.000000")
    assert summary.blocked_policy_count == d("1.000000")
    assert summary.material_policy_count == d("2.000000")
    assert summary.stale_policy_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.low_agreement_count == d("1.000000")
    assert summary.missing_review_count == d("1.000000")
    assert summary.slow_review_count == d("1.000000")
    assert summary.average_materiality_score == d("0.246667")
    assert summary.max_policy_age_seconds == d("108000.000000")
    assert summary.average_public_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.policy_status, row.policy_area) for row in summary.rows) == (
        ("blocked", "evaluation_rules"),
        ("watch", "archived_rules"),
        ("ready", "frontier_model_rules"),
    )

    blocked = summary.rows[0]
    assert blocked.policy_age_seconds == d("10800.000000")
    assert blocked.review_lag_seconds is None
    assert blocked.probability_change == d("0.150000")
    assert blocked.redacted_policy_reference == "sha256:6d7d8e64aca3"
    assert blocked.reason_codes == (
        "market_research_ai_safety_policy_digest_material_block",
        "market_research_ai_safety_policy_digest_missing_review",
        "market_research_ai_safety_policy_digest_probability_shift",
    )

    watch = summary.rows[1]
    assert watch.policy_age_seconds == d("108000.000000")
    assert watch.review_lag_seconds == d("93600.000000")
    assert watch.redacted_policy_reference == "sha256:6e67b2ee9080"
    assert watch.reason_codes == (
        "market_research_ai_safety_policy_digest_low_agreement",
        "market_research_ai_safety_policy_digest_material_watch",
        "market_research_ai_safety_policy_digest_slow_review",
        "market_research_ai_safety_policy_digest_stale_policy",
        "market_research_ai_safety_policy_digest_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.policy_status == "ready"
    assert ready.policy_age_seconds == d("2700.000000")
    assert ready.review_lag_seconds == d("1800.000000")
    assert ready.redacted_policy_reference == "public-policy-memo"
    assert ready.reason_codes == (
        "market_research_ai_safety_policy_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_material_block",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
        ),
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_missing_review",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
        ),
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_probability_shift",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
        ),
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_low_agreement",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
        ),
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_material_watch",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
        ),
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_slow_review",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
        ),
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_stale_policy",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
        ),
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_thin_sources",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
        ),
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_ready",
            count=d("1.000000"),
            policy_ratio=d("0.333333"),
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
        "confidential-policy-brief",
        "credential",
    ):
        assert value not in public


def test_empty_ai_safety_policy_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.next_step == "block_report_only_market_research_ai_safety_policy_digest"
    assert summary.policy_count == ZERO
    assert summary.ready_policy_count == ZERO
    assert summary.watch_policy_count == ZERO
    assert summary.blocked_policy_count == ZERO
    assert summary.average_materiality_score == ZERO
    assert summary.max_policy_age_seconds == ZERO
    assert summary.average_public_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
        MarketResearchAiSafetyPolicyDigestReasonCodeCount(
            reason_code="market_research_ai_safety_policy_digest_no_inputs",
            count=d("1.000000"),
            policy_ratio=d("1.000000"),
        ),
    )
    assert summary.reason_codes == (
        "market_research_ai_safety_policy_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_ai_safety_policy_digest_honors_custom_threshold_config() -> None:
    summary = report(
        (input_row(impact_materiality_score=d("0.120000")),),
        cfg=config(
            fresh_policy_max_age_seconds=d("172800.000000"),
            min_public_source_count=d("1"),
            min_cross_source_agreement=d("0.100000"),
            materiality_watch_threshold=d("0.100000"),
            materiality_block_threshold=d("0.900000"),
            max_review_lag_seconds=d("172800.000000"),
        ),
    )

    assert summary.digest_status == "watch"
    assert summary.watch_policy_count == d("1.000000")
    assert summary.rows[0].policy_status == "watch"
    assert summary.rows[0].reason_codes == (
        "market_research_ai_safety_policy_digest_material_watch",
    )


def test_ai_safety_policy_digest_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = market_research_ai_safety_policy_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["policy_count"] == "1.000000"
    assert payload["average_materiality_score"] == "0.120000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_policy_reference':" not in repr(payload)
    assert "confidential" not in repr(payload).lower()


def test_ai_safety_policy_digest_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchAiSafetyPolicyDigestConfig)
    assert is_dataclass(MarketResearchAiSafetyPolicyDigestInputRow)
    assert is_dataclass(MarketResearchAiSafetyPolicyDigestRow)
    assert is_dataclass(MarketResearchAiSafetyPolicyDigestReasonCodeCount)
    assert is_dataclass(MarketResearchAiSafetyPolicyDigestReport)

    cfg = config()
    source_row = input_row()
    summary = report((source_row,), cfg=cfg)
    with pytest.raises(FrozenInstanceError):
        cfg.config_version = "changed"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source_row.public_source_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.reason_code_counts[0].count = d("4")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.policy_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("ai-safety-policy-v0"))
    with pytest.raises(ValueError, match="fresh_policy_max_age_seconds"):
        config(fresh_policy_max_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="min_cross_source_agreement"):
        config(min_cross_source_agreement=Decimal("NaN"))
    with pytest.raises(ValueError, match="materiality_watch_threshold"):
        config(materiality_watch_threshold=d("-0.000001"))
    with pytest.raises(ValueError, match="materiality_block_threshold"):
        config(
            materiality_watch_threshold=d("0.500000"),
            materiality_block_threshold=d("0.350000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        config(readonly=False)
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="live_surface")
    with pytest.raises(ValueError, match="policy_observed_at"):
        input_row(policy_observed_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="reviewed_at"):
        input_row(reviewed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="public_source_count"):
        input_row(public_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cross_source_agreement"):
        input_row(cross_source_agreement=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="impact_materiality_score"):
        input_row(impact_materiality_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="market_probability_before"):
        input_row(market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="market_probability_after"):
        input_row(market_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        input_row(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        input_row(readonly=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_ai_safety_policy_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_ai_safety_policy_digest(
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
                "market_research_ai_safety_policy_digest_ready",
                "market_research_ai_safety_policy_digest_material_watch",
            ),
        )
    with pytest.raises(ValueError, match="policy_status"):
        replace(ready, policy_status="blocked")
    with pytest.raises(ValueError, match="probability_change"):
        replace(ready, probability_change=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_policy_reference"):
        replace(ready, redacted_policy_reference="https://host?credential=hidden")

    with pytest.raises(ValueError, match="ready_policy_count"):
        replace(report((input_row(),)), ready_policy_count=ZERO)
    with pytest.raises(ValueError, match="paper_only"):
        replace(report((input_row(),)), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(report((input_row(),)), report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report((input_row(),)), readonly=False)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.ai.safety.z", policy_area="zeta_rules"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    source_row = input_row()
    summary = report((source_row,))

    assert_decimal_numeric_fields(source_row)
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
