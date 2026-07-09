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
    "research_strategy_team_domain_signal_allocation_report"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/"
    "research_strategy_team_domain_signal_allocation_report.py",
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
            module.DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION
        ),
        "attention_block_threshold": d("0.750000"),
        "attention_watch_threshold": d("0.500000"),
        "calibration_decay_window_hours": d("72.000000"),
        "high_information_yield_threshold": d("0.800000"),
        "fresh_calibration_threshold": d("0.700000"),
        "event_urgency_threshold": d("0.700000"),
        "liquidity_cost_pressure_threshold": d("0.650000"),
        "evidence_gap_threshold": d("0.600000"),
        "information_yield_weight": d("0.300000"),
        "calibration_freshness_weight": d("0.200000"),
        "event_urgency_weight": d("0.200000"),
        "liquidity_cost_pressure_weight": d("0.150000"),
        "evidence_gap_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamDomainSignalAllocationConfig(**values)


def domain_signal(
    module: Any,
    domain_team: str = "macro_policy_alpha",
    analyst_lane: str = "macro_policy",
    **overrides: object,
) -> Any:
    values = {
        "domain_team": domain_team,
        "analyst_lane": analyst_lane,
        "calibration_checked_at": GENERATED_AT - timedelta(hours=6),
        "information_yield_score": d("0.900000"),
        "event_urgency_score": d("0.800000"),
        "liquidity_cost_pressure_score": d("0.700000"),
        "unresolved_evidence_gap_score": d("0.600000"),
    }
    values.update(overrides)
    return module.ResearchStrategyTeamDomainSignalAllocationInput(**values)


def report(
    module: Any,
    rows: tuple[Any, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    cfg: Any | None = None,
) -> Any:
    return module.build_research_strategy_team_domain_signal_allocation_report(
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


def resign_payload(module: Any, payload: dict[str, object]) -> dict[str, object]:
    payload["validation_digest"] = module._digest_from_mapping(payload)  # noqa: SLF001
    return payload


def resign_row(module: Any, row: dict[str, object]) -> dict[str, object]:
    row["validation_digest"] = module._digest_from_mapping(row)  # noqa: SLF001
    return row


def test_allocates_and_ranks_domain_team_attention_scores() -> None:
    module = api()
    result = report(
        module,
        (
            domain_signal(
                module,
                "sports_injury_gamma",
                "sports_health",
                calibration_checked_at=GENERATED_AT - timedelta(hours=96),
                information_yield_score=d("0.300000"),
                event_urgency_score=d("0.200000"),
                liquidity_cost_pressure_score=d("0.200000"),
                unresolved_evidence_gap_score=d("0.300000"),
            ),
            domain_signal(
                module,
                "macro_policy_alpha",
                "macro_policy",
                calibration_checked_at=GENERATED_AT - timedelta(hours=6),
                information_yield_score=d("0.900000"),
                event_urgency_score=d("0.800000"),
                liquidity_cost_pressure_score=d("0.700000"),
                unresolved_evidence_gap_score=d("0.600000"),
            ),
            domain_signal(
                module,
                "climate_weather_beta",
                "weather_events",
                calibration_checked_at=GENERATED_AT - timedelta(hours=36),
                information_yield_score=d("0.650000"),
                event_urgency_score=d("0.500000"),
                liquidity_cost_pressure_score=d("0.450000"),
                unresolved_evidence_gap_score=d("0.550000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert is_dataclass(result)
    assert type(result) is module.ResearchStrategyTeamDomainSignalAllocationReport
    assert result.generated_at == GENERATED_AT
    assert result.generated_at.tzinfo is UTC
    assert result.status == "block"
    assert result.domain_team_count == d("3.000000")
    assert result.pass_count == d("1.000000")
    assert result.watch_count == d("1.000000")
    assert result.block_count == d("1.000000")
    assert result.average_attention_need_score == d("0.519444")
    assert result.highest_attention_need_score == d("0.808333")
    assert result.average_information_yield_score == d("0.616667")
    assert result.average_calibration_freshness_score == d("0.472222")
    assert result.average_event_urgency_score == d("0.500000")
    assert result.average_liquidity_cost_pressure_score == d("0.450000")
    assert result.average_unresolved_evidence_gap_score == d("0.483333")
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True

    assert tuple(row.domain_team for row in result.rows) == (
        "macro_policy_alpha",
        "climate_weather_beta",
        "sports_injury_gamma",
    )
    assert tuple(row.allocation_rank for row in result.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in result.rows) == ("block", "watch", "pass")

    blocked = result.rows[0]
    assert blocked.calibration_age_hours == d("6.000000")
    assert blocked.calibration_freshness_score == d("0.916667")
    assert blocked.attention_need_score == d("0.808333")
    assert blocked.reason_codes == (
        "attention_score_block",
        "high_information_yield",
        "calibration_freshness_current",
        "event_urgency_high",
        "liquidity_cost_pressure_high",
        "evidence_gap_unresolved",
    )
    assert_digest(blocked.validation_digest)

    watched = result.rows[1]
    assert watched.calibration_age_hours == d("36.000000")
    assert watched.calibration_freshness_score == d("0.500000")
    assert watched.attention_need_score == d("0.545000")
    assert watched.reason_codes == ("attention_score_watch",)

    passed = result.rows[2]
    assert passed.calibration_age_hours == d("96.000000")
    assert passed.calibration_freshness_score == ZERO
    assert passed.attention_need_score == d("0.205000")
    assert passed.reason_codes == ("attention_score_pass",)


def test_public_payload_is_deterministic_and_digest_validated() -> None:
    module = api()
    rows = (
        domain_signal(module, "macro_policy_alpha", "macro_policy"),
        domain_signal(
            module,
            "climate_weather_beta",
            "weather_events",
            calibration_checked_at=GENERATED_AT - timedelta(hours=36),
            information_yield_score=d("0.650000"),
            event_urgency_score=d("0.500000"),
            liquidity_cost_pressure_score=d("0.450000"),
            unresolved_evidence_gap_score=d("0.550000"),
        ),
    )
    result_a = report(module, rows)
    result_b = report(module, tuple(reversed(rows)))

    payload_a = result_a.public_payload
    payload_b = module.research_strategy_team_domain_signal_allocation_report_public_payload(
        result_b,
    )
    encoded = json.dumps(payload_a, sort_keys=True, allow_nan=False)

    assert payload_a == payload_b
    assert result_a.validation_digest == result_b.validation_digest
    assert payload_a["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert payload_a["domain_team_count"] == "2.000000"
    assert payload_a["rows"][0]["attention_need_score"] == "0.808333"
    assert payload_a["rows"][0]["allocation_rank"] == "1.000000"
    assert payload_a["validation_digest"] == result_a.validation_digest
    assert_digest(result_a.validation_digest)
    assert not any(type(value) is Decimal for value in walk(payload_a))
    assert not any(type(value) is int for value in walk(payload_a))
    assert not any(type(value) is float for value in walk(payload_a))
    assert ": 1.0" not in encoded

    assert (
        module.research_strategy_team_domain_signal_allocation_report_public_payload(
            payload_a,
        )
        == payload_a
    )

    tampered = dict(payload_a)
    tampered["domain_team_count"] = "3.000000"
    with pytest.raises(ValueError, match="validation_digest"):
        module.research_strategy_team_domain_signal_allocation_report_public_payload(
            tampered,
        )
    with pytest.raises(ValueError, match="validation_digest"):
        replace(result_a.rows[0], validation_digest="0" * 64)
    with pytest.raises(ValueError, match="attention_need_score"):
        replace(result_a.rows[0], attention_need_score=d("0.100000"))
    with pytest.raises(ValueError, match="validation_digest"):
        replace(result_a, validation_digest="0" * 64)


def test_public_payload_prevents_raw_private_and_execution_surface_leaks() -> None:
    module = api()
    result = report(module, (domain_signal(module),))
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
        domain_signal(module, "raw-candidate-id/market-slug?token=hidden")

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
            module.research_strategy_team_domain_signal_allocation_report_public_payload(
                {**payload, unsafe_key: unsafe_value},
            )

    for unsafe_value in (
        "https://example.test/raw",
        "postgresql://example",
        "token-secret",
        "wallet-address",
        "live-trading",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_team_domain_signal_allocation_report_public_payload(
                {**payload, "analyst_lane": unsafe_value},
            )


def test_public_payload_rejects_fresh_digest_schema_tampering() -> None:
    module = api()
    payload = report(module, (domain_signal(module),)).public_payload

    extra_report_field = resign_payload(
        module,
        {**payload, "diagnostic_summary": "pass"},
    )
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.research_strategy_team_domain_signal_allocation_report_public_payload(
            extra_report_field,
        )

    extra_row_field = dict(payload)
    extra_row_field["rows"] = [dict(payload["rows"][0])]
    extra_row_field["rows"][0]["diagnostic_summary"] = "pass"
    resign_row(module, extra_row_field["rows"][0])
    resign_payload(module, extra_row_field)
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.research_strategy_team_domain_signal_allocation_report_public_payload(
            extra_row_field,
        )

    extra_reason_count_field = dict(payload)
    extra_reason_count_field["reason_code_counts"] = [
        dict(payload["reason_code_counts"][0]),
    ]
    extra_reason_count_field["reason_code_counts"][0]["diagnostic_summary"] = "pass"
    resign_payload(module, extra_reason_count_field)
    with pytest.raises(ValueError, match="unexpected public payload field"):
        module.research_strategy_team_domain_signal_allocation_report_public_payload(
            extra_reason_count_field,
        )

    malformed_decimal_text = dict(payload)
    malformed_decimal_text["domain_team_count"] = "1"
    resign_payload(module, malformed_decimal_text)
    with pytest.raises(ValueError, match="domain_team_count"):
        module.research_strategy_team_domain_signal_allocation_report_public_payload(
            malformed_decimal_text,
        )


def test_custom_config_thresholds_and_validation_change_statuses() -> None:
    module = api()
    watched_input = domain_signal(
        module,
        "climate_weather_beta",
        "weather_events",
        calibration_checked_at=GENERATED_AT - timedelta(hours=36),
        information_yield_score=d("0.650000"),
        event_urgency_score=d("0.500000"),
        liquidity_cost_pressure_score=d("0.450000"),
        unresolved_evidence_gap_score=d("0.550000"),
    )
    default_report = report(module, (watched_input,))
    strict_report = report(
        module,
        (watched_input,),
        cfg=config(
            module,
            attention_block_threshold=d("0.900000"),
            attention_watch_threshold=d("0.600000"),
        ),
    )

    assert default_report.rows[0].attention_need_score == d("0.545000")
    assert default_report.rows[0].status == "watch"
    assert strict_report.rows[0].attention_need_score == d("0.545000")
    assert strict_report.rows[0].status == "pass"
    assert strict_report.reason_codes == ("attention_score_pass",)

    with pytest.raises(ValueError, match="attention_block_threshold"):
        config(module, attention_block_threshold=d("0.400000"))
    with pytest.raises(ValueError, match="weights"):
        config(module, information_yield_weight=d("0.350000"))
    with pytest.raises(ValueError, match="calibration_decay_window_hours"):
        config(module, calibration_decay_window_hours=d("0.000000"))
    with pytest.raises(ValueError, match="config_version"):
        config(
            module,
            config_version=_StringSubclass(
                module.DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION,
            ),
        )


def test_validation_requires_frozen_exact_decimals_flags_and_report_only_scope() -> None:
    module = api()
    cfg = config(module)
    item = domain_signal(module)
    result = report(module, (item,), cfg=cfg)

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_DOMAIN_SIGNAL_ALLOCATION_REPORT_CONFIG_VERSION",
        "ResearchStrategyTeamDomainSignalAllocationConfig",
        "ResearchStrategyTeamDomainSignalAllocationInput",
        "ResearchStrategyTeamDomainSignalAllocationReasonCodeCount",
        "ResearchStrategyTeamDomainSignalAllocationReport",
        "ResearchStrategyTeamDomainSignalAllocationRow",
        "build_research_strategy_team_domain_signal_allocation_report",
        "research_strategy_team_domain_signal_allocation_report_public_payload",
    )

    for cls in (
        module.ResearchStrategyTeamDomainSignalAllocationConfig,
        module.ResearchStrategyTeamDomainSignalAllocationInput,
        module.ResearchStrategyTeamDomainSignalAllocationReasonCodeCount,
        module.ResearchStrategyTeamDomainSignalAllocationRow,
        module.ResearchStrategyTeamDomainSignalAllocationReport,
    ):
        assert is_dataclass(cls)

    with pytest.raises(FrozenInstanceError):
        cfg.attention_block_threshold = d("0.800000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        item.information_yield_score = d("0.100000")  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        result.rows[0].status = "pass"  # type: ignore[misc]

    for value in (cfg, item, result, *result.rows, *result.reason_code_counts):
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for field in fields(value):
            field_value = getattr(value, field.name)
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if field.name.endswith(("_count", "_rank", "_score", "_hours", "_ratio")):
                assert type(field_value) is Decimal

    with pytest.raises(ValueError, match="attention_block_threshold"):
        config(module, attention_block_threshold=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="attention_watch_threshold"):
        config(module, attention_watch_threshold=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="domain_team"):
        domain_signal(module, _StringSubclass("macro_policy_alpha"))
    with pytest.raises(ValueError, match="information_yield_score"):
        domain_signal(module, information_yield_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_urgency_score"):
        domain_signal(module, event_urgency_score=Decimal("NaN"))
    with pytest.raises(ValueError, match="unresolved_evidence_gap_score"):
        domain_signal(module, unresolved_evidence_gap_score=d("1.000001"))
    with pytest.raises(ValueError, match="calibration_checked_at"):
        domain_signal(
            module,
            calibration_checked_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(module, (), generated_at=datetime(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="inputs"):
        report(module, (object(),))
    with pytest.raises(ValueError, match="calibration_checked_at"):
        report(
            module,
            (
                domain_signal(
                    module,
                    calibration_checked_at=GENERATED_AT + timedelta(minutes=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="paper_only"):
        domain_signal(module, paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(result, readonly=False)
    with pytest.raises(ValueError, match="pass, watch, or block"):
        replace(result.rows[0], status="blocked")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            result.rows[0],
            reason_codes=("attention_score_block", "attention_score_watch"),
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
        module.ResearchStrategyTeamDomainSignalAllocationConfig,
        module.ResearchStrategyTeamDomainSignalAllocationInput,
        module.ResearchStrategyTeamDomainSignalAllocationReasonCodeCount,
        module.ResearchStrategyTeamDomainSignalAllocationRow,
        module.ResearchStrategyTeamDomainSignalAllocationReport,
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
