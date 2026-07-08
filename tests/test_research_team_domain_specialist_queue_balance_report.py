from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


REPO_ROOT = Path(__file__).resolve().parents[1]
MODULE_PATH = (
    REPO_ROOT
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_domain_specialist_queue_balance_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 8, 17, 30, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_team_domain_specialist_queue_balance_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode(
        "utf-8",
    )
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-domain-specialist-queue-balance-report-v0",
        "watch_backlog_pressure_ratio": d("0.750000"),
        "block_backlog_pressure_ratio": d("1.250000"),
        "watch_review_latency_seconds": d("3600.000000"),
        "block_review_latency_seconds": d("10800.000000"),
        "watch_calibration_feedback_age_seconds": d("604800.000000"),
        "block_calibration_feedback_age_seconds": d("1209600.000000"),
        "watch_memory_conflict_ratio": d("0.200000"),
        "block_memory_conflict_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistQueueBalanceConfig(**values)


def domain_signal(domain_label: str = "macro_policy", **overrides: object):
    module = api()
    values = {
        "domain_label": domain_label,
        "pending_backlog_count": d("3.000000"),
        "domain_capacity_count": d("10.000000"),
        "review_latency_seconds": d("900.000000"),
        "calibration_feedback_age_seconds": d("3600.000000"),
        "memory_conflict_count": d("0.000000"),
        "memory_item_count": d("10.000000"),
        "observed_at": OBSERVED_AT,
    }
    values.update(overrides)
    return module.ResearchTeamDomainSpecialistQueueBalanceInput(**values)


def build_report(*items: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_domain_specialist_queue_balance_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def walk_payload(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_payload(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_payload(item))
        return tuple(nested)
    return (value,)


def assert_no_unsafe_public_surface(value: object) -> None:
    forbidden = (
        "raw",
        "candidate",
        "market",
        "slug",
        "question",
        "url",
        "source",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "buy",
        "sell",
        "recommendation",
        "sizing",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lower_key = key.lower()
            assert not any(fragment in lower_key for fragment in forbidden), lower_key
            assert_no_unsafe_public_surface(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_unsafe_public_surface(item)
        return
    if isinstance(value, str):
        lower_value = value.lower()
        assert not any(fragment in lower_value for fragment in forbidden), lower_value


def assert_decimal_fields_are_plain(value: object) -> None:
    for field in fields(value):
        item = getattr(value, field.name)
        if isinstance(item, Decimal):
            assert type(item) is Decimal, field.name


def test_queue_balance_rolls_up_sanitized_domain_aggregates_and_digest() -> None:
    rows = (
        domain_signal("macro_policy"),
        domain_signal(
            "sports_injury",
            pending_backlog_count=d("9.000000"),
            review_latency_seconds=d("4500.000000"),
            calibration_feedback_age_seconds=d("700000.000000"),
            memory_conflict_count=d("3.000000"),
        ),
        domain_signal(
            "crypto_protocols",
            pending_backlog_count=d("15.000000"),
            review_latency_seconds=d("12000.000000"),
            calibration_feedback_age_seconds=d("1500000.000000"),
            memory_conflict_count=d("6.000000"),
        ),
    )

    report = build_report(
        *rows,
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )
    reversed_report = build_report(*reversed(rows))

    assert api().QUEUE_BALANCE_STATUSES == ("pass", "watch", "block")
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.status == "block"
    assert report.queue_balance_mode == "paper_queue_balance_block"
    assert report.domain_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.imbalanced_domain_count == d("2.000000")
    assert report.average_backlog_pressure_ratio == d("0.900000")
    assert report.max_backlog_pressure_ratio == d("1.500000")
    assert report.average_review_latency_seconds == d("5800.000000")
    assert report.max_review_latency_seconds == d("12000.000000")
    assert report.average_calibration_feedback_age_seconds == d("734533.333333")
    assert report.max_calibration_feedback_age_seconds == d("1500000.000000")
    assert report.average_memory_conflict_ratio == d("0.300000")
    assert report.max_memory_conflict_ratio == d("0.600000")
    assert report.max_queue_balance_score == d("1.000000")
    assert report.reason_codes == (
        "queue_balance_report_block",
        "queue_balance_backlog_pressure_block",
        "queue_balance_review_latency_block",
        "queue_balance_calibration_feedback_freshness_block",
        "queue_balance_memory_conflict_load_block",
        "queue_balance_backlog_pressure_watch",
        "queue_balance_review_latency_watch",
        "queue_balance_calibration_feedback_freshness_watch",
        "queue_balance_memory_conflict_load_watch",
    )

    blocked, watched, passed = report.rows
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert tuple(row.domain_label for row in report.rows) == (
        "crypto_protocols",
        "sports_injury",
        "macro_policy",
    )
    assert blocked.backlog_pressure_ratio == d("1.500000")
    assert blocked.memory_conflict_ratio == d("0.600000")
    assert blocked.queue_balance_score == d("1.000000")
    assert blocked.observation_age_seconds == d("1800.000000")
    assert blocked.reason_codes == (
        "queue_balance_backlog_pressure_block",
        "queue_balance_review_latency_block",
        "queue_balance_calibration_feedback_freshness_block",
        "queue_balance_memory_conflict_load_block",
    )
    assert watched.queue_balance_score == d("0.720000")
    assert watched.reason_codes == (
        "queue_balance_backlog_pressure_watch",
        "queue_balance_review_latency_watch",
        "queue_balance_calibration_feedback_freshness_watch",
        "queue_balance_memory_conflict_load_watch",
    )
    assert passed.reason_codes == ("queue_balance_domain_clear",)

    reason_counts = {item.reason_code: item for item in report.reason_code_counts}
    assert reason_counts["queue_balance_backlog_pressure_block"].count == d("1.000000")
    assert reason_counts["queue_balance_backlog_pressure_block"].domain_ratio == d(
        "0.333333",
    )
    assert reason_counts["queue_balance_domain_clear"].count == d("1.000000")

    payload = api().research_team_domain_specialist_queue_balance_report_payload(report)
    reversed_payload = api().research_team_domain_specialist_queue_balance_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T18:00:00+00:00"
    assert payload["rows"][0]["domain_label"] == "crypto_protocols"
    assert payload["rows"][0]["queue_balance_score"] == "1.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert all(type(item) is not Decimal for item in walk_payload(payload))
    assert all(type(item) not in (int, float) for item in walk_payload(payload))
    assert_no_unsafe_public_surface(payload)
    json.dumps(payload, sort_keys=True)


def test_empty_report_and_public_contract_are_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_TEAM_DOMAIN_SPECIALIST_QUEUE_BALANCE_CONFIG_VERSION",
        "QUEUE_BALANCE_STATUSES",
        "ResearchTeamDomainSpecialistQueueBalanceConfig",
        "ResearchTeamDomainSpecialistQueueBalanceInput",
        "ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount",
        "ResearchTeamDomainSpecialistQueueBalanceReport",
        "ResearchTeamDomainSpecialistQueueBalanceRow",
        "build_research_team_domain_specialist_queue_balance_report",
        "research_team_domain_specialist_queue_balance_report_digest",
        "research_team_domain_specialist_queue_balance_report_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    report = build_report()

    assert report.status == "pass"
    assert report.queue_balance_mode == "paper_queue_balance_monitor"
    assert report.domain_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.imbalanced_domain_count == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("queue_balance_no_domains",)
    assert report.reason_code_counts == (
        module.ResearchTeamDomainSpecialistQueueBalanceReasonCodeCount(
            reason_code="queue_balance_no_domains",
            count=d("1.000000"),
            domain_ratio=d("1.000000"),
        ),
    )
    assert module.research_team_domain_specialist_queue_balance_report_payload(
        report,
    )["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_tamper_evident() -> None:
    module = api()
    cfg = config()
    signal = domain_signal()
    report = build_report(signal, cfg=cfg)

    for value in (cfg, signal, report, *report.rows, *report.reason_code_counts):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        assert_decimal_fields_are_plain(value)

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclass"):
        type("BadRow", (module.ResearchTeamDomainSpecialistQueueBalanceRow,), {})
    with pytest.raises(ValueError, match="Decimal"):
        domain_signal(pending_backlog_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        domain_signal(review_latency_seconds=900.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        domain_signal(memory_conflict_count=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="observed_at"):
        domain_signal(observed_at=datetime(2026, 7, 8, 17, 30))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(domain_signal(), generated_at=_DatetimeSubclass(2026, 7, 8, 18, 0))
    with pytest.raises(ValueError, match="public aggregate label"):
        domain_signal("market_slug")
    with pytest.raises(ValueError, match="public aggregate label"):
        domain_signal("source_text")
    with pytest.raises(ValueError, match="public aggregate label"):
        domain_signal("table_name")
    with pytest.raises(ValueError, match="unique"):
        build_report(domain_signal("macro_policy"), domain_signal("macro_policy"))
    with pytest.raises(ValueError, match="memory_conflict_count"):
        domain_signal(memory_conflict_count=d("11.000000"))
    with pytest.raises(ValueError, match="block_backlog_pressure_ratio"):
        config(
            watch_backlog_pressure_ratio=d("1.500000"),
            block_backlog_pressure_ratio=d("1.250000"),
        )
    with pytest.raises(ValueError, match="paper_only"):
        domain_signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    object.__setattr__(report.rows[0], "queue_balance_score", d("0.990000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_specialist_queue_balance_report_payload(report)


def test_payload_rejects_unsafe_keys_values_flags_numbers_and_digest_tampering() -> None:
    module = api()
    payload = module.research_team_domain_specialist_queue_balance_report_payload(
        build_report(domain_signal()),
    )

    for key in (
        "raw_candidate_id",
        "market_id",
        "market_slug",
        "question_text",
        "source_text",
        "source_url",
        "dsn",
        "table_name",
        "auth_token",
        "wallet_address",
        "order_id",
        "trade_id",
        "live_url",
        "position_sizing",
        "recommendation_id",
    ):
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_domain_specialist_queue_balance_report_payload(unsafe)

    for value in (
        "raw candidate",
        "market slug",
        "question text",
        "source text",
        "postgres dsn",
        "table name",
        "auth token",
        "wallet signer",
        "order route",
        "trade route",
        "live execution",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = [value]
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_domain_specialist_queue_balance_report_payload(unsafe)

    numeric = dict(payload)
    numeric["domain_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_domain_specialist_queue_balance_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["readonly"] = False
    with pytest.raises(ValueError, match="readonly"):
        module.research_team_domain_specialist_queue_balance_report_payload(downgraded)

    tampered = dict(payload)
    tampered["status"] = "watch"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_domain_specialist_queue_balance_report_payload(tampered)

    assert module.research_team_domain_specialist_queue_balance_report_digest(payload) == (
        payload["derived_validation_digest"]
    )


def test_module_has_no_external_or_live_execution_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)
    banned_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "subprocess",
        "urllib",
        "web3",
        "py_clob_client",
    }
    banned_call_names = {
        "connect",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "send",
        "submit",
        "get",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "insert",
        "upsert",
        "order",
        "trade",
        "buy",
        "sell",
        "write",
        "write_text",
        "write_bytes",
        "open",
        "float",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in banned_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in banned_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in banned_call_names
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    exported_surface = "\n".join(api().__all__).lower()
    for forbidden in (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "recommendation",
        "sizing",
    ):
        assert forbidden not in exported_surface
