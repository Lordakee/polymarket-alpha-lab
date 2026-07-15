from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_information_source_yield_curve_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_information_source_yield_curve_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def config(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_INFORMATION_SOURCE_YIELD_CURVE_REPORT_CONFIG_VERSION
        ),
        "yield_score_block_threshold": d("0.700000"),
        "yield_score_watch_threshold": d("0.450000"),
        "freshness_decay_window_hours": d("24.000000"),
        "high_authority_confidence_threshold": d("0.800000"),
        "high_conflict_reduction_threshold": d("0.700000"),
        "review_effort_constraint_threshold": d("0.650000"),
        "freshness_weight": d("0.350000"),
        "authority_confidence_weight": d("0.300000"),
        "conflict_reduction_weight": d("0.250000"),
        "review_efficiency_weight": d("0.100000"),
    }
    values.update(overrides)
    return module.ResearchStrategyInformationSourceYieldCurveConfig(**values)


def source_category(
    module: Any,
    source_category: str = "official_filings",
    **overrides: object,
) -> Any:
    values = {
        "source_category": source_category,
        "last_observed_at": GENERATED_AT - timedelta(hours=6),
        "authority_confidence_score": d("0.900000"),
        "conflict_reduction_score": d("0.800000"),
        "review_effort_score": d("0.200000"),
    }
    values.update(overrides)
    return module.ResearchStrategyInformationSourceYieldCurveInput(**values)


def report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: Any | None = None,
) -> Any:
    return module.build_research_strategy_information_source_yield_curve_report(
        rows,
        generated_at=generated_at,
        config=cfg or config(module),
    )


def walk(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        children: list[Any] = []
        for child in value.values():
            children.extend(walk(child))
        return tuple(children)
    if isinstance(value, list):
        children = []
        for child in value:
            children.extend(walk(child))
        return tuple(children)
    return (value,)


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def test_ranks_sanitized_source_categories_by_yield_decay_over_time() -> None:
    module = api()
    result = report(
        module,
        (
            source_category(
                module,
                "specialist_blogs",
                last_observed_at=GENERATED_AT - timedelta(hours=48),
                authority_confidence_score=d("0.500000"),
                conflict_reduction_score=d("0.300000"),
                review_effort_score=d("0.800000"),
            ),
            source_category(
                module,
                "official_filings",
                last_observed_at=GENERATED_AT - timedelta(hours=6),
                authority_confidence_score=d("0.900000"),
                conflict_reduction_score=d("0.800000"),
                review_effort_score=d("0.200000"),
            ),
            source_category(
                module,
                "expert_roundups",
                last_observed_at=GENERATED_AT - timedelta(hours=18),
                authority_confidence_score=d("0.700000"),
                conflict_reduction_score=d("0.600000"),
                review_effort_score=d("0.400000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(result)
    assert type(result) is module.ResearchStrategyInformationSourceYieldCurveReport
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.status == "block"
    assert result.source_category_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_expected_information_yield_score == d("0.521667")
    assert result.highest_expected_information_yield_score == d("0.812500")
    assert result.average_freshness_yield_score == d("0.333333")
    assert result.average_authority_confidence_score == d("0.700000")
    assert result.average_conflict_reduction_score == d("0.566667")
    assert result.average_review_effort_score == d("0.466667")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.source_category for row in result.rows) == (
        "official_filings",
        "expert_roundups",
        "specialist_blogs",
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")

    blocked = result.rows[0]
    assert blocked.observation_age_hours == d("6.000000")
    assert blocked.freshness_yield_score == d("0.750000")
    assert blocked.review_efficiency_score == d("0.800000")
    assert blocked.expected_information_yield_score == d("0.812500")
    assert blocked.reason_codes == (
        "yield_score_block",
        "high_authority_confidence",
        "high_conflict_reduction",
    )
    assert_digest(blocked.validation_digest)

    watched = result.rows[1]
    assert watched.observation_age_hours == d("18.000000")
    assert watched.freshness_yield_score == d("0.250000")
    assert watched.expected_information_yield_score == d("0.507500")
    assert watched.reason_codes == ("yield_score_watch",)

    passed = result.rows[2]
    assert passed.observation_age_hours == d("48.000000")
    assert passed.freshness_yield_score == ZERO
    assert passed.expected_information_yield_score == d("0.245000")
    assert passed.reason_codes == (
        "yield_score_pass",
        "review_effort_constraint",
    )


def test_public_payload_is_deterministic_and_digest_validated() -> None:
    module = api()
    rows = (
        source_category(module, "official_filings"),
        source_category(
            module,
            "expert_roundups",
            last_observed_at=GENERATED_AT - timedelta(hours=18),
            authority_confidence_score=d("0.700000"),
            conflict_reduction_score=d("0.600000"),
            review_effort_score=d("0.400000"),
        ),
    )
    result_a = report(module, rows)
    result_b = report(module, tuple(reversed(rows)))

    payload_a = result_a.public_payload
    payload_b = module.research_strategy_information_source_yield_curve_report_public_payload(
        result_b,
    )
    encoded = json.dumps(payload_a, sort_keys=True, allow_nan=False)

    assert payload_a == payload_b
    assert result_a.validation_digest == result_b.validation_digest
    assert payload_a["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert payload_a["source_category_count"] == "2.000000"
    assert payload_a["rows"][0]["expected_information_yield_score"] == "0.812500"
    assert payload_a["validation_digest"] == result_a.validation_digest
    assert_digest(result_a.validation_digest)
    assert not any(type(value) is Decimal for value in walk(payload_a))
    assert not any(type(value) is int for value in walk(payload_a))
    assert not any(type(value) is float for value in walk(payload_a))
    assert ": 1.0" not in encoded

    assert (
        module.research_strategy_information_source_yield_curve_report_public_payload(
            payload_a,
        )
        == payload_a
    )

    tampered = dict(payload_a)
    tampered["source_category_count"] = "3.000000"
    with pytest.raises(ValueError, match="validation_digest"):
        module.research_strategy_information_source_yield_curve_report_public_payload(
            tampered,
        )
    with pytest.raises(ValueError, match="validation_digest"):
        replace(result_a.rows[0], validation_digest="0" * 64)
    with pytest.raises(ValueError, match="expected_information_yield_score"):
        replace(result_a.rows[0], expected_information_yield_score=d("0.100000"))
    with pytest.raises(ValueError, match="validation_digest"):
        replace(result_a, validation_digest="0" * 64)


def test_public_payload_prevents_raw_private_and_trading_surface_leaks() -> None:
    module = api()
    result = report(module, (source_category(module),))
    payload = result.public_payload
    rendered = repr(payload).casefold()

    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth_surface",
        "authentication",
        "order",
        "trade",
        "position",
        "sizing",
        "buy",
        "sell",
        "recommend",
        "live",
        "https://",
        "://",
    ):
        assert forbidden not in rendered

    with pytest.raises(ValueError, match="unsafe"):
        source_category(module, "raw-candidate-id/market-slug?token=hidden")

    for unsafe_key, unsafe_value in (
        ("candidate_id", "hidden"),
        ("market_slug", "hidden"),
        ("source_url", "hidden"),
        ("source_text", "hidden"),
        ("dsn", "hidden"),
        ("table_name", "hidden"),
        ("token", "hidden"),
        ("wallet", "hidden"),
        ("order_surface", "hidden"),
        ("trade_surface", "hidden"),
        ("live_surface", "hidden"),
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_information_source_yield_curve_report_public_payload(
                {**payload, unsafe_key: unsafe_value},
            )

    for unsafe_value in (
        "https://example.test/raw-source",
        "postgresql://example",
        "token-secret",
        "wallet-address",
        "live-trading",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_information_source_yield_curve_report_public_payload(
                {**payload, "analyst_note": unsafe_value},
            )


def test_custom_config_thresholds_change_status_without_changing_inputs() -> None:
    module = api()
    source = source_category(
        module,
        "expert_roundups",
        last_observed_at=GENERATED_AT - timedelta(hours=18),
        authority_confidence_score=d("0.700000"),
        conflict_reduction_score=d("0.600000"),
        review_effort_score=d("0.400000"),
    )
    default_report = report(module, (source,))
    strict_report = report(
        module,
        (source,),
        cfg=config(
            module,
            yield_score_block_threshold=d("0.900000"),
            yield_score_watch_threshold=d("0.600000"),
        ),
    )

    assert default_report.rows[0].expected_information_yield_score == d("0.507500")
    assert default_report.rows[0].status == "watch"
    assert strict_report.rows[0].expected_information_yield_score == d("0.507500")
    assert strict_report.rows[0].status == "pass"
    assert strict_report.reason_codes == ("yield_score_pass",)


def test_validation_requires_exact_decimals_frozen_flags_and_safe_statuses() -> None:
    module = api()
    cfg = config(module)
    source = source_category(module)
    result = report(module, (source,), cfg=cfg)

    for cls in (
        module.ResearchStrategyInformationSourceYieldCurveConfig,
        module.ResearchStrategyInformationSourceYieldCurveInput,
        module.ResearchStrategyInformationSourceYieldCurveReasonCodeCount,
        module.ResearchStrategyInformationSourceYieldCurveRow,
        module.ResearchStrategyInformationSourceYieldCurveReport,
    ):
        assert is_dataclass(cls)

    with pytest.raises(FrozenInstanceError):
        cfg.yield_score_block_threshold = d("0.800000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        source.authority_confidence_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_INFORMATION_SOURCE_YIELD_CURVE_REPORT_CONFIG_VERSION,
            ),
        )
    with pytest.raises(ValueError, match="yield_score_block_threshold"):
        config(module, yield_score_block_threshold=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="yield_score_watch_threshold"):
        config(module, yield_score_watch_threshold=_DecimalSubclass("0.450000"))
    with pytest.raises(ValueError, match="yield_score_block_threshold"):
        config(module, yield_score_block_threshold=d("0.400000"))
    with pytest.raises(ValueError, match="weights"):
        config(module, freshness_weight=d("0.400000"))
    with pytest.raises(ValueError, match="source_category"):
        source_category(module, _StringSubclass("official_filings"))
    with pytest.raises(ValueError, match="authority_confidence_score"):
        source_category(module, authority_confidence_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="conflict_reduction_score"):
        source_category(module, conflict_reduction_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="review_effort_score"):
        source_category(module, review_effort_score=d("1.000001"))
    with pytest.raises(ValueError, match="last_observed_at"):
        source_category(
            module,
            last_observed_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(module, (), generated_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="inputs"):
        report(module, (object(),))
    with pytest.raises(ValueError, match="last_observed_at"):
        report(
            module,
            (
                source_category(
                    module,
                    last_observed_at=GENERATED_AT + timedelta(minutes=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        source_category(module, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="pass, watch, or block"):
        replace(result.rows[0], status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            result.rows[0],
            reason_codes=("yield_score_block", "yield_score_watch"),
        )


def test_module_scope_is_report_only_without_io_or_trading_surfaces() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_INFORMATION_SOURCE_YIELD_CURVE_REPORT_CONFIG_VERSION",
        "ResearchStrategyInformationSourceYieldCurveConfig",
        "ResearchStrategyInformationSourceYieldCurveInput",
        "ResearchStrategyInformationSourceYieldCurveReasonCodeCount",
        "ResearchStrategyInformationSourceYieldCurveReport",
        "ResearchStrategyInformationSourceYieldCurveRow",
        "build_research_strategy_information_source_yield_curve_report",
        "research_strategy_information_source_yield_curve_report_public_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned_imports = {
        "asyncio",
        "http",
        "httpx",
        "os",
        "pathlib",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
    }
    banned_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "send",
        "submit",
        "update",
        "urlopen",
        "write",
    }
    banned_attributes = banned_calls | {"commit", "rollback", "session"}

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    for cls in (
        module.ResearchStrategyInformationSourceYieldCurveConfig,
        module.ResearchStrategyInformationSourceYieldCurveInput,
        module.ResearchStrategyInformationSourceYieldCurveReasonCodeCount,
        module.ResearchStrategyInformationSourceYieldCurveRow,
        module.ResearchStrategyInformationSourceYieldCurveReport,
    ):
        for field in fields(cls):
            lowered_name = field.name.lower()
            for forbidden in (
                "candidate",
                "market",
                "slug",
                "question",
                "url",
                "text",
                "dsn",
                "table",
                "token",
                "wallet",
                "order",
                "trade",
                "live",
                "sizing",
                "recommend",
            ):
                assert forbidden not in lowered_name
