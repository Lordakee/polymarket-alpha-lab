from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import importlib
import inspect
import json
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_market_context_completeness_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(**overrides: object) -> Any:
    module = api()
    values = {
        "config_version": "research-strategy-market-context-completeness-report-test",
        "min_sanitized_evidence_count": d("4.000000"),
        "sanitized_evidence_count_pass_floor": d("6.000000"),
        "min_independent_family_count": d("2.000000"),
        "independent_family_count_pass_floor": d("3.000000"),
        "section_watch_floor": d("0.700000"),
        "section_block_floor": d("0.400000"),
        "aggregate_watch_floor": d("0.750000"),
        "aggregate_block_floor": d("0.500000"),
        "open_context_gap_watch_ceiling": d("0.000000"),
        "open_context_gap_block_ceiling": d("2.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMarketContextCompletenessConfig(**values)


def context_input(**overrides: object) -> Any:
    module = api()
    values = {
        "review_label": "context-alpha",
        "sanitized_evidence_count": d("7.000000"),
        "independent_family_count": d("4.000000"),
        "evidence_section_completeness": d("0.900000"),
        "cost_section_completeness": d("0.880000"),
        "settlement_rule_section_completeness": d("0.910000"),
        "domain_memory_section_completeness": d("0.860000"),
        "forecast_rationale_section_completeness": d("0.920000"),
        "open_context_gap_count": d("0.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategyMarketContextCompletenessInput(**values)


def build_report(*items: Any, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_strategy_market_context_completeness_report(
        items,
        config=cfg(),
        generated_at=generated_at,
    )


def assert_digest(value: object) -> None:
    assert type(value) is str
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_no_float_or_int(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
        return
    assert type(value) not in (float, int)


def public_forbidden_terms() -> tuple[str, ...]:
    return (
        "candidate_id",
        "candidate-id",
        "market_id",
        "market-id",
        "market_slug",
        "slug",
        "question",
        "source_text",
        "source-url",
        "source_url",
        "http://",
        "https://",
        "://",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )


def assert_public_payload_safe(value: object) -> None:
    rendered = json.dumps(value, sort_keys=True).lower()
    assert [term for term in public_forbidden_terms() if term in rendered] == []


def status_values(value: object) -> tuple[str, ...]:
    found: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            if key == "status":
                found.append(item)
            found.extend(status_values(item))
    elif isinstance(value, list):
        for item in value:
            found.extend(status_values(item))
    return tuple(found)


def test_report_aggregates_context_sections_for_manual_review_only() -> None:
    report = build_report(
        context_input(review_label="context-pass"),
        context_input(
            review_label="context-watch",
            sanitized_evidence_count=d("4.000000"),
            independent_family_count=d("2.000000"),
            evidence_section_completeness=d("0.720000"),
            cost_section_completeness=d("0.680000"),
            settlement_rule_section_completeness=d("0.760000"),
            domain_memory_section_completeness=d("0.690000"),
            forecast_rationale_section_completeness=d("0.710000"),
            open_context_gap_count=d("1.000000"),
        ),
        context_input(
            review_label="context-block",
            sanitized_evidence_count=d("1.000000"),
            independent_family_count=d("0.000000"),
            evidence_section_completeness=d("0.300000"),
            cost_section_completeness=d("0.200000"),
            settlement_rule_section_completeness=d("0.390000"),
            domain_memory_section_completeness=d("0.300000"),
            forecast_rationale_section_completeness=d("0.350000"),
            open_context_gap_count=d("2.000000"),
        ),
    )

    rows = {row.review_label: row for row in report.rows}
    assert tuple(row.review_label for row in report.rows) == (
        "context-block",
        "context-watch",
        "context-pass",
    )
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert rows["context-pass"].context_completeness_score == d("0.924286")
    assert rows["context-pass"].reason_codes == ("market_context_completeness_pass",)
    assert rows["context-watch"].evidence_count_ratio == d("0.666667")
    assert rows["context-watch"].independent_family_ratio == d("0.666667")
    assert rows["context-watch"].context_completeness_score == d("0.699048")
    assert rows["context-watch"].reason_codes == (
        "sanitized_evidence_count_watch",
        "independent_family_count_watch",
        "cost_section_watch",
        "domain_memory_section_watch",
        "aggregate_context_watch",
        "open_context_gap_watch",
    )
    assert rows["context-block"].context_completeness_score == d("0.243810")
    assert rows["context-block"].reason_codes == (
        "sanitized_evidence_count_block",
        "independent_family_count_block",
        "evidence_section_block",
        "cost_section_block",
        "settlement_rule_section_block",
        "domain_memory_section_block",
        "forecast_rationale_section_block",
        "aggregate_context_block",
        "open_context_gap_block",
    )

    assert report.context_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.status == "block"
    assert report.manual_review_state == "manual_review_block"
    assert report.min_context_completeness_score == d("0.243810")
    assert report.average_context_completeness_score == d("0.622381")
    assert report.reason_codes == (
        "sanitized_evidence_count_block",
        "independent_family_count_block",
        "evidence_section_block",
        "cost_section_block",
        "settlement_rule_section_block",
        "domain_memory_section_block",
        "forecast_rationale_section_block",
        "aggregate_context_block",
        "open_context_gap_block",
        "market_context_completeness_block",
        "sanitized_evidence_count_watch",
        "independent_family_count_watch",
        "cost_section_watch",
        "domain_memory_section_watch",
        "aggregate_context_watch",
        "open_context_gap_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_digest(report.derived_validation_digest)


def test_payload_is_canonical_deterministic_decimal_only_and_safe() -> None:
    module = api()
    first = build_report(
        context_input(review_label="context-watch", cost_section_completeness=d("0.680000")),
        context_input(review_label="context-pass"),
    )
    second = build_report(
        context_input(review_label="context-pass"),
        context_input(review_label="context-watch", cost_section_completeness=d("0.680000")),
    )

    first_payload = module.research_strategy_market_context_completeness_report_payload(first)
    second_payload = module.research_strategy_market_context_completeness_report_payload(
        second,
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first_payload == second_payload
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["context_count"] == "2.000000"
    assert first_payload["rows"][0]["review_label"] == "context-watch"
    assert first_payload["rows"][0]["cost_section_completeness"] == "0.680000"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert status_values(first_payload) == ("watch", "watch", "pass")
    assert set(status_values(first_payload)) <= {"pass", "watch", "block"}
    assert module.validate_research_strategy_market_context_completeness_report_payload(
        first_payload,
    )
    assert (
        module.research_strategy_market_context_completeness_report_payload(first_payload)
        == first_payload
    )
    assert_no_float_or_int(first_payload)
    assert_public_payload_safe(first_payload)
    json.dumps(first_payload, sort_keys=True, allow_nan=False)


def test_empty_report_blocks_manual_review_without_side_effect_surface() -> None:
    report = build_report()

    assert report.context_count == d("0.000000")
    assert report.pass_count == d("0.000000")
    assert report.watch_count == d("0.000000")
    assert report.block_count == d("0.000000")
    assert report.min_context_completeness_score is None
    assert report.average_context_completeness_score == d("0.000000")
    assert report.status == "block"
    assert report.manual_review_state == "manual_review_block"
    assert report.reason_codes == ("market_context_completeness_no_contexts",)
    assert report.rows == ()
    assert_digest(report.derived_validation_digest)


def test_frozen_strict_decimal_only_and_hard_flags() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_MARKET_CONTEXT_COMPLETENESS_REPORT_CONFIG_VERSION",
        "ResearchStrategyMarketContextCompletenessConfig",
        "ResearchStrategyMarketContextCompletenessInput",
        "ResearchStrategyMarketContextCompletenessRow",
        "ResearchStrategyMarketContextCompletenessReport",
        "build_research_strategy_market_context_completeness_report",
        "research_strategy_market_context_completeness_report_payload",
        "validate_research_strategy_market_context_completeness_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    report = build_report(context_input())
    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].context_completeness_score = d("0.000000")  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchStrategyMarketContextCompletenessConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeInput(module.ResearchStrategyMarketContextCompletenessInput):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchStrategyMarketContextCompletenessRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchStrategyMarketContextCompletenessReport):
            pass

    with pytest.raises(ValueError, match="paper_only"):
        context_input(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        cfg(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="sanitized_evidence_count"):
        context_input(sanitized_evidence_count=4)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cost_section_completeness"):
        context_input(cost_section_completeness=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="forecast_rationale_section_completeness"):
        context_input(
            forecast_rationale_section_completeness=DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="independent_family_count"):
        context_input(
            sanitized_evidence_count=d("1.000000"),
            independent_family_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(context_input(), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            context_input(),
            generated_at=DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="sanitized_evidence_count_pass_floor"):
        cfg(
            min_sanitized_evidence_count=d("6.000000"),
            sanitized_evidence_count_pass_floor=d("4.000000"),
        )
    with pytest.raises(ValueError, match="section_watch_floor"):
        cfg(section_watch_floor=d("0.300000"), section_block_floor=d("0.400000"))

    for item in (cfg(), context_input(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if isinstance(value, tuple):
                continue
            assert type(value) is not int, field.name
            assert type(value) is not float, field.name


def test_digest_and_consistency_validation_reject_tampering() -> None:
    module = api()
    report = build_report(context_input())
    row = report.rows[0]

    with pytest.raises(ValueError, match="context_completeness_score"):
        replace(row, context_completeness_score=row.context_completeness_score - d("0.000001"))
    with pytest.raises(ValueError, match="status"):
        replace(row, status="block")
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(build_report(context_input(review_label="context-z")).rows[0], row))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    payload = module.research_strategy_market_context_completeness_report_payload(report)
    tampered_payload = dict(payload)
    tampered_payload["context_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_strategy_market_context_completeness_report_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "context_completeness_score", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_market_context_completeness_report_payload(report)


def test_public_payload_rejects_raw_identifier_text_and_action_surfaces() -> None:
    module = api()

    for term in public_forbidden_terms():
        with pytest.raises(ValueError, match="unsafe public"):
            context_input(review_label=f"context-{term}")

    payload = module.research_strategy_market_context_completeness_report_payload(
        build_report(context_input()),
    )
    for key in (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_text",
        "source_url",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
        "position_size",
    ):
        unsafe_payload = dict(payload)
        unsafe_payload[key] = "forbidden"
        with pytest.raises(ValueError, match="unsafe public"):
            module.validate_research_strategy_market_context_completeness_report_payload(
                unsafe_payload,
            )

    unsafe_value_payload = dict(payload)
    unsafe_value_payload["review_label"] = "https://example.invalid/context"
    with pytest.raises(ValueError, match="unsafe public"):
        module.validate_research_strategy_market_context_completeness_report_payload(
            unsafe_value_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["context_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_research_strategy_market_context_completeness_report_payload(
            numeric_payload,
        )

    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.validate_research_strategy_market_context_completeness_report_payload(
            flag_payload,
        )


def test_module_has_no_storage_network_wallet_order_or_trading_surface() -> None:
    module = api()
    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    forbidden_name_fragments = (
        "candidateid",
        "marketid",
        "marketslug",
        "question",
        "sourcetext",
        "sourceurl",
        "dsn",
        "tablename",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
    )
    for public_name in public_names:
        normalized_name = public_name.lower().replace("_", "")
        assert [
            fragment
            for fragment in forbidden_name_fragments
            if fragment in normalized_name
        ] == []

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "supabase",
        "Path(",
        "open(",
        ".write(",
        ".read(",
        "submit",
        "execute",
        "private_key",
        "wallet",
        "position_size",
    ):
        assert forbidden not in source

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
        "urllib",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "send",
        "submit",
        "write",
        "write_bytes",
        "write_text",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
