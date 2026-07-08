from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_edge_decay_monitor_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 11, 45, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_edge_decay_monitor_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-strategy-edge-decay-monitor-report-test-v0",
        "watch_probability_delta_age_seconds": d("900.000000"),
        "block_probability_delta_age_seconds": d("1800.000000"),
        "watch_evidence_freshness_floor": d("0.650000"),
        "block_evidence_freshness_floor": d("0.350000"),
        "watch_cost_drift_score": d("0.250000"),
        "block_cost_drift_score": d("0.500000"),
        "watch_contradiction_pressure_score": d("0.300000"),
        "block_contradiction_pressure_score": d("0.650000"),
    }
    values.update(overrides)
    return module.ResearchStrategyEdgeDecayMonitorReportConfig(**values)


def observation(**overrides: object):
    module = api()
    values = {
        "monitor_bucket": "macro_policy",
        "observed_at": OBSERVED_AT,
        "probability_delta_age_seconds": d("1200.000000"),
        "evidence_freshness_score": d("0.500000"),
        "cost_drift_score": d("0.300000"),
        "contradiction_pressure_score": d("0.400000"),
    }
    values.update(overrides)
    return module.ResearchStrategyEdgeDecayMonitorObservation(**values)


def report(*, observations=(), cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_edge_decay_monitor_report(
        observations,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
    )


def assert_no_float_or_int_values(value: Any) -> None:
    if isinstance(value, float) or type(value) is int:
        raise AssertionError(f"unexpected public numeric value {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            assert_no_float_or_int_values(item)


def test_report_aggregates_strategy_edge_decay_pressure_without_decisions() -> None:
    module = api()
    digest = report(
        observations=(
            observation(
                monitor_bucket="macro_policy",
                observed_at=datetime(
                    2026,
                    7,
                    8,
                    7,
                    45,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                probability_delta_age_seconds=d("1200.000000"),
                evidence_freshness_score=d("0.500000"),
                cost_drift_score=d("0.300000"),
                contradiction_pressure_score=d("0.400000"),
            ),
            observation(
                monitor_bucket="macro_policy",
                probability_delta_age_seconds=d("2400.000000"),
                evidence_freshness_score=d("0.300000"),
                cost_drift_score=d("0.550000"),
                contradiction_pressure_score=d("0.700000"),
            ),
            observation(
                monitor_bucket="sports_news",
                probability_delta_age_seconds=d("300.000000"),
                evidence_freshness_score=d("0.900000"),
                cost_drift_score=d("0.100000"),
                contradiction_pressure_score=d("0.100000"),
            ),
        ),
    )

    assert is_dataclass(digest)
    assert type(digest) is module.ResearchStrategyEdgeDecayMonitorReport
    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == "research-strategy-edge-decay-monitor-report-test-v0"
    assert digest.observation_count == d("3")
    assert digest.bucket_count == d("2")
    assert digest.watch_bucket_count == d("0")
    assert digest.block_bucket_count == d("1")
    assert digest.average_probability_delta_age_seconds == d("1300.000000")
    assert digest.minimum_evidence_freshness_score == d("0.300000")
    assert digest.maximum_cost_drift_score == d("0.550000")
    assert digest.maximum_contradiction_pressure_score == d("0.700000")
    assert digest.maximum_edge_decay_pressure_score == d("0.800000")
    assert digest.status == "block"
    assert digest.reason_codes == (
        "strategy_edge_decay_block",
        "probability_delta_age_block",
        "evidence_freshness_block",
        "cost_drift_block",
        "contradiction_pressure_block",
    )
    assert digest.paper_only is True
    assert digest.report_only is True
    assert digest.readonly is True

    assert tuple(row.monitor_bucket for row in digest.bucket_rows) == (
        "macro_policy",
        "sports_news",
    )
    blocked, passed = digest.bucket_rows
    assert blocked.status == "block"
    assert blocked.observation_count == d("2")
    assert blocked.average_probability_delta_age_seconds == d("1800.000000")
    assert blocked.minimum_evidence_freshness_score == d("0.300000")
    assert blocked.maximum_cost_drift_score == d("0.550000")
    assert blocked.maximum_contradiction_pressure_score == d("0.700000")
    assert blocked.edge_decay_pressure_score == d("0.800000")
    assert blocked.reason_codes == (
        "strategy_edge_decay_block",
        "probability_delta_age_block",
        "evidence_freshness_block",
        "cost_drift_block",
        "contradiction_pressure_block",
    )
    assert passed.status == "pass"
    assert passed.edge_decay_pressure_score == d("0.100000")
    assert passed.reason_codes == ("strategy_edge_decay_pass",)


def test_empty_report_is_pass_with_decimal_fields_and_hard_flags() -> None:
    empty = report()

    assert empty.observation_count == ZERO
    assert empty.bucket_count == ZERO
    assert empty.watch_bucket_count == ZERO
    assert empty.block_bucket_count == ZERO
    assert empty.average_probability_delta_age_seconds == ZERO
    assert empty.minimum_evidence_freshness_score == ZERO
    assert empty.maximum_cost_drift_score == ZERO
    assert empty.maximum_contradiction_pressure_score == ZERO
    assert empty.maximum_edge_decay_pressure_score == ZERO
    assert empty.status == "pass"
    assert empty.reason_codes == ("strategy_edge_decay_monitor_clear",)
    assert empty.bucket_rows == ()
    assert empty.paper_only is True
    assert empty.report_only is True
    assert empty.readonly is True

    populated = report(observations=(observation(),))
    for value in (empty, populated, *populated.bucket_rows):
        for item in fields(value):
            if item.name in {"paper_only", "report_only", "readonly"}:
                continue
            item_value = getattr(value, item.name)
            if item.name.endswith(
                (
                    "_count",
                    "_seconds",
                    "_score",
                ),
            ):
                assert type(item_value) is Decimal


def test_payload_is_stable_sanitized_decimal_string_only_and_digest_validated() -> None:
    module = api()
    digest = report(observations=(observation(),))
    payload = module.research_strategy_edge_decay_monitor_report_payload(digest)

    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["observation_count"] == "1"
    assert payload["average_probability_delta_age_seconds"] == "1200.000000"
    assert payload["bucket_rows"][0]["edge_decay_pressure_score"] == "0.500000"
    assert type(payload["derived_validation_digest"]) is str
    assert len(payload["derived_validation_digest"]) == 64
    assert int(payload["derived_validation_digest"], 16) >= 0
    assert_no_float_or_int_values(payload)
    assert module.research_strategy_edge_decay_monitor_report_payload(payload) == payload

    unsigned = dict(payload)
    digest_value = unsigned.pop("derived_validation_digest")
    expected = hashlib.sha256(
        json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(),
    ).hexdigest()
    assert digest_value == expected

    tampered = {**payload, "status": "pass"}
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_strategy_edge_decay_monitor_report_payload(tampered)

    with pytest.raises(ValueError, match="Decimal-derived"):
        module.research_strategy_edge_decay_monitor_report_payload(
            {**payload, "observation_count": 1},
        )

    with pytest.raises(ValueError, match="float"):
        module.research_strategy_edge_decay_monitor_report_payload(
            {**payload, "maximum_cost_drift_score": 0.1},
        )


def test_public_payload_rejects_raw_identifiers_urls_sources_and_live_surfaces() -> None:
    module = api()
    payload = module.research_strategy_edge_decay_monitor_report_payload(
        report(observations=(observation(),)),
    )
    forbidden_tokens = (
        "candidate",
        "market_id",
        "slug",
        "question",
        "url",
        "source_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "size",
        "live",
        "auth",
    )
    lowered_payload = repr(payload).lower()
    assert all(token not in lowered_payload for token in forbidden_tokens)

    for unsafe_key in (
        "raw_candidate_id",
        "market_slug",
        "question_text",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "auth_token",
        "wallet_address",
        "order_id",
        "trade_id",
        "recommended_size",
        "live_trading_enabled",
    ):
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_edge_decay_monitor_report_payload(
                {**payload, unsafe_key: "redacted"},
            )

    for unsafe_value in (
        "candidate-123",
        "https://example.test/market",
        "raw source text",
        "postgres://dsn",
        "wallet-token",
        "buy now",
        "sell signal",
        "recommendation",
    ):
        bad_row = {**payload["bucket_rows"][0], "monitor_bucket": unsafe_value}
        with pytest.raises(ValueError, match="unsafe"):
            module.research_strategy_edge_decay_monitor_report_payload(
                {**payload, "bucket_rows": [bad_row]},
            )


def test_dataclasses_are_frozen_strict_decimal_utc_and_status_guarded() -> None:
    module = api()
    digest = report(observations=(observation(),))

    with pytest.raises(FrozenInstanceError):
        digest.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.bucket_rows[0].status = "pass"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        config(watch_cost_drift_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="Decimal"):
        observation(probability_delta_age_seconds=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 8, 11, 45))
    with pytest.raises(ValueError, match="UTC offset"):
        observation(
            observed_at=datetime(
                2026,
                7,
                8,
                11,
                45,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC))
    with pytest.raises(ValueError, match="status"):
        replace(digest, status="empty")
    with pytest.raises(ValueError, match="duplicate monitor_bucket"):
        report(
            observations=(
                observation(monitor_bucket="macro_policy"),
                observation(monitor_bucket="macro_policy", observed_at=OBSERVED_AT),
            ),
        )
    with pytest.raises(ValueError, match="config"):
        module.build_research_strategy_edge_decay_monitor_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )


def test_module_scope_is_pure_report_only_without_trading_persistence_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imports: set[str] = set()
    call_names: set[str] = set()
    attribute_names: set[str] = set()

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imports.add(node.module)
        elif isinstance(node, ast.Call):
            name = _call_name(node.func)
            if name is not None:
                call_names.add(name.rsplit(".", maxsplit=1)[-1])
        elif isinstance(node, ast.Attribute):
            attribute_names.add(node.attr)

    forbidden_import_fragments = (
        "api",
        "auth",
        "broker",
        "client",
        "clob",
        "db",
        "env",
        "http",
        "network",
        "order",
        "psycopg",
        "request",
        "socket",
        "sql",
        "store",
        "supabase",
        "urllib",
        "wallet",
    )
    forbidden_call_or_attribute_names = {
        "buy",
        "cancel",
        "close",
        "commit",
        "connect",
        "cursor",
        "environ",
        "execute",
        "executemany",
        "fetch",
        "getenv",
        "insert",
        "open",
        "order",
        "persist",
        "recommend",
        "rollback",
        "send",
        "sell",
        "sign",
        "size",
        "submit",
        "trade",
        "write",
    }

    assert imports
    assert all(
        fragment not in imported.lower()
        for imported in imports
        for fragment in forbidden_import_fragments
    )
    assert not (call_names & forbidden_call_or_attribute_names)
    assert not (attribute_names & forbidden_call_or_attribute_names)


def test_public_api_exports_report_contract() -> None:
    module = api()

    assert module.__all__ == (
        "ResearchStrategyEdgeDecayMonitorObservation",
        "ResearchStrategyEdgeDecayMonitorReportConfig",
        "ResearchStrategyEdgeDecayMonitorReport",
        "ResearchStrategyEdgeDecayMonitorBucket",
        "build_research_strategy_edge_decay_monitor_report",
        "research_strategy_edge_decay_monitor_report_payload",
        "validate_research_strategy_edge_decay_monitor_public_payload",
    )


def _call_name(node: ast.AST) -> str | None:
    if isinstance(node, ast.Name):
        return node.id
    if isinstance(node, ast.Attribute):
        base = _call_name(node.value)
        return f"{base}.{node.attr}" if base else node.attr
    return None
