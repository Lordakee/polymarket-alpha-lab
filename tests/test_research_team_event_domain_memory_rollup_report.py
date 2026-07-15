from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
OBSERVED_AT = GENERATED_AT - timedelta(hours=3)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/research_team_event_domain_memory_rollup_report.py",
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def api():
    return import_module(
        "polymarket_alpha_lab.research_team_event_domain_memory_rollup_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def domain_signal(domain_key: str, **overrides: object):
    module = api()
    values = {
        "domain_key": domain_key,
        "calibration_freshness_ratio": d("0.950000"),
        "feedback_absorption_ratio": d("0.900000"),
        "evidence_coverage_ratio": d("0.920000"),
        "review_backlog_count": d("1"),
        "observed_at": OBSERVED_AT,
        "sanitized_memory_confirmed": True,
    }
    values.update(overrides)
    return module.ResearchTeamEventDomainMemoryRollupInput(**values)


def config(**overrides: object):
    module = api()
    values = {
        "config_version": "research-team-event-domain-memory-rollup-report-v0",
        "pass_health_threshold": d("0.850000"),
        "watch_health_threshold": d("0.650000"),
        "calibration_watch_threshold": d("0.700000"),
        "calibration_block_threshold": d("0.400000"),
        "feedback_watch_threshold": d("0.700000"),
        "feedback_block_threshold": d("0.400000"),
        "evidence_watch_threshold": d("0.700000"),
        "evidence_block_threshold": d("0.400000"),
        "review_backlog_watch_count": d("5"),
        "review_backlog_block_count": d("12"),
        "calibration_weight": d("0.300000"),
        "feedback_weight": d("0.250000"),
        "evidence_weight": d("0.300000"),
        "backlog_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchTeamEventDomainMemoryRollupConfig(**values)


def build_report(*items: object, cfg: object | None = None, generated_at=GENERATED_AT):
    module = api()
    return module.build_research_team_event_domain_memory_rollup_report(
        items,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_no_public_numbers(value: Any) -> None:
    if type(value) in (int, float):
        raise AssertionError(f"unexpected public numeric value: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_numbers(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_public_numbers(item)


def public_keys(value: Any) -> tuple[str, ...]:
    if isinstance(value, dict):
        keys: list[str] = []
        for key, item in value.items():
            keys.append(key)
            keys.extend(public_keys(item))
        return tuple(keys)
    if isinstance(value, list):
        keys = []
        for item in value:
            keys.extend(public_keys(item))
        return tuple(keys)
    return ()


def test_rolls_up_sanitized_memory_health_across_event_domains() -> None:
    module = api()

    report = build_report(
        domain_signal("politics"),
        domain_signal(
            "btc",
            calibration_freshness_ratio=d("0.680000"),
            feedback_absorption_ratio=d("0.780000"),
            evidence_coverage_ratio=d("0.720000"),
            review_backlog_count=d("6"),
        ),
        domain_signal(
            "indices",
            calibration_freshness_ratio=d("0.320000"),
            feedback_absorption_ratio=d("0.350000"),
            evidence_coverage_ratio=d("0.300000"),
            review_backlog_count=d("14"),
        ),
        domain_signal("gold"),
        domain_signal(
            "soccer",
            evidence_coverage_ratio=d("0.650000"),
            review_backlog_count=d("5"),
        ),
        domain_signal(
            "basketball",
            feedback_absorption_ratio=d("0.600000"),
            review_backlog_count=d("3"),
        ),
    )

    assert type(report) is module.ResearchTeamEventDomainMemoryRollupReport
    assert is_dataclass(report)
    assert module.EVENT_DOMAIN_MEMORY_ROLLUP_STATUSES == ("pass", "watch", "block")
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-team-event-domain-memory-rollup-report-v0"
    )
    assert report.domain_count == d("6")
    assert report.pass_count == d("2")
    assert report.watch_count == d("3")
    assert report.block_count == d("1")
    assert report.status == "block"
    assert report.average_domain_memory_health_score == d("0.767512")
    assert report.lowest_domain_memory_health_score == d("0.273500")
    assert report.max_review_backlog_count == d("14")
    assert report.fresh_calibration_domain_count == d("4")
    assert report.feedback_absorbed_domain_count == d("4")
    assert report.evidence_ready_domain_count == d("4")
    assert report.reason_codes == (
        "event_domain_memory_rollup_block",
        "calibration_freshness_block",
        "feedback_absorption_block",
        "evidence_coverage_block",
        "review_backlog_block",
        "calibration_freshness_watch",
        "feedback_absorption_watch",
        "evidence_coverage_watch",
        "review_backlog_watch",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.domain_key for row in report.rows) == (
        "indices",
        "btc",
        "soccer",
        "basketball",
        "gold",
        "politics",
    )
    assert tuple(row.row_status for row in report.rows) == (
        "block",
        "watch",
        "watch",
        "watch",
        "pass",
        "pass",
    )
    assert report.rows[0] == module.ResearchTeamEventDomainMemoryRollupRow(
        domain_key="indices",
        calibration_freshness_ratio=d("0.320000"),
        feedback_absorption_ratio=d("0.350000"),
        evidence_coverage_ratio=d("0.300000"),
        review_backlog_count=d("14"),
        backlog_health_score=d("0.000000"),
        domain_memory_health_score=d("0.273500"),
        row_status="block",
        observed_at=OBSERVED_AT,
        reason_codes=(
            "calibration_freshness_block",
            "feedback_absorption_block",
            "evidence_coverage_block",
            "review_backlog_block",
        ),
    )
    assert report.rows[1].domain_memory_health_score == d("0.743571")
    assert report.rows[1].reason_codes == (
        "calibration_freshness_watch",
        "review_backlog_watch",
    )
    assert report.rows[-1].reason_codes == ("event_domain_memory_pass",)


def test_payload_digest_is_deterministic_and_decimal_only() -> None:
    module = api()
    first = build_report(
        domain_signal(
            "btc",
            observed_at=datetime(
                2026,
                7,
                8,
                4,
                30,
                tzinfo=timezone(timedelta(hours=-7)),
            ),
        ),
        domain_signal("politics"),
        generated_at=datetime(
            2026,
            7,
            8,
            5,
            0,
            tzinfo=timezone(timedelta(hours=-7)),
        ),
    )
    second = build_report(
        domain_signal("politics"),
        domain_signal("btc", observed_at=datetime(2026, 7, 8, 11, 30, tzinfo=UTC)),
    )

    payload = module.research_team_event_domain_memory_rollup_report_payload(first)
    repeat_payload = module.research_team_event_domain_memory_rollup_report_payload(
        second,
    )

    assert first.derived_validation_digest == second.derived_validation_digest
    assert payload == repeat_payload
    assert payload == first.payload
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["domain_count"] == "2"
    assert payload["rows"][0]["domain_key"] == "btc"
    assert payload["rows"][0]["observed_at"] == "2026-07-08T11:30:00+00:00"
    assert payload["rows"][0]["domain_memory_health_score"] == "0.936000"
    assert payload["derived_validation_digest"] == first.derived_validation_digest
    assert len(first.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in first.derived_validation_digest)
    assert_no_public_numbers(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)

    tampered = dict(payload)
    tampered["pass_count"] = "1"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_event_domain_memory_rollup_report_payload(tampered)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, pass_count=d("1"))


def test_public_payload_prevents_raw_identifier_and_surface_leaks() -> None:
    module = api()
    payload = module.research_team_event_domain_memory_rollup_report_payload(
        build_report(domain_signal("gold")),
    )

    forbidden_fragments = (
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "order",
        "trade",
        "recommendation",
        "sizing",
    )
    assert not any(
        fragment in key.lower()
        for key in public_keys(payload)
        for fragment in forbidden_fragments
    )
    payload_text = repr(payload).lower()
    assert not any(fragment in payload_text for fragment in forbidden_fragments)

    for key in forbidden_fragments:
        unsafe = dict(payload)
        unsafe[key] = "redacted"
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_event_domain_memory_rollup_report_payload(unsafe)

    for value in (
        "candidate_id",
        "market slug",
        "raw question",
        "source url",
        "source text",
        "dsn",
        "table name",
        "auth token",
        "wallet route",
        "order surface",
        "live trade",
        "recommendation",
        "sizing",
    ):
        unsafe = dict(payload)
        unsafe["reason_codes"] = (value,)
        with pytest.raises(ValueError, match="unsafe public"):
            module.research_team_event_domain_memory_rollup_report_payload(unsafe)

    numeric = dict(payload)
    numeric["domain_count"] = 1
    with pytest.raises(ValueError, match="numeric"):
        module.research_team_event_domain_memory_rollup_report_payload(numeric)

    downgraded = dict(payload)
    downgraded["paper_only"] = False
    with pytest.raises(ValueError, match="paper_only"):
        module.research_team_event_domain_memory_rollup_report_payload(downgraded)


def test_custom_thresholds_change_domain_status_and_rollup_digest() -> None:
    custom = config(
        pass_health_threshold=d("0.920000"),
        watch_health_threshold=d("0.800000"),
        calibration_watch_threshold=d("0.900000"),
        calibration_block_threshold=d("0.500000"),
        feedback_watch_threshold=d("0.850000"),
        feedback_block_threshold=d("0.500000"),
        evidence_watch_threshold=d("0.900000"),
        evidence_block_threshold=d("0.500000"),
        review_backlog_watch_count=d("2"),
        review_backlog_block_count=d("7"),
    )

    signal = domain_signal("basketball", feedback_absorption_ratio=d("0.800000"))
    report = build_report(signal, cfg=custom)
    default_report = build_report(signal)

    assert report.status == "watch"
    assert report.pass_count == d("0")
    assert report.watch_count == d("1")
    assert report.block_count == d("0")
    assert report.reason_codes == (
        "event_domain_memory_rollup_watch",
        "feedback_absorption_watch",
    )
    assert report.rows[0].reason_codes == ("feedback_absorption_watch",)
    assert report.derived_validation_digest != default_report.derived_validation_digest


def test_validation_enforces_frozen_decimal_datetime_and_materialized_fields() -> None:
    module = api()
    report = build_report(domain_signal("soccer"))

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="Decimal"):
        domain_signal("soccer", review_backlog_count=1)
    with pytest.raises(ValueError, match="Decimal"):
        domain_signal("soccer", evidence_coverage_ratio=0.9)
    with pytest.raises(ValueError, match="Decimal"):
        domain_signal(
            "soccer",
            calibration_freshness_ratio=_DecimalSubclass("0.900000"),
        )
    with pytest.raises(ValueError, match="whole Decimal"):
        domain_signal("soccer", review_backlog_count=d("1.500000"))
    with pytest.raises(ValueError, match="observed_at"):
        domain_signal("soccer", observed_at=datetime(2026, 7, 8, 11, 0))
    with pytest.raises(ValueError, match="observed_at"):
        domain_signal(
            "soccer",
            observed_at=_DatetimeSubclass(2026, 7, 8, 11, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="domain_key"):
        domain_signal(_StringSubclass("soccer"))
    with pytest.raises(ValueError, match="public-safe"):
        domain_signal("market_slug")
    with pytest.raises(ValueError, match="sanitized_memory_confirmed"):
        domain_signal("soccer", sanitized_memory_confirmed=False)
    with pytest.raises(ValueError, match="generated_at"):
        build_report(domain_signal("soccer"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="future"):
        build_report(
            domain_signal("soccer", observed_at=GENERATED_AT + timedelta(seconds=1)),
        )
    with pytest.raises(ValueError, match="unique"):
        build_report(domain_signal("soccer"), domain_signal("soccer"))
    with pytest.raises(ValueError, match="config"):
        build_report(domain_signal("soccer"), cfg=object())
    with pytest.raises(ValueError, match="threshold"):
        config(pass_health_threshold=d("0.600000"))
    with pytest.raises(ValueError, match="weight"):
        config(backlog_weight=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        module.ResearchTeamEventDomainMemoryRollupReport(
            **{
                **report.__dict__,
                "status": "block",
            },
        )

    object.__setattr__(report.rows[0], "evidence_coverage_ratio", d("0.100000"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_team_event_domain_memory_rollup_report_payload(report)


def test_module_is_report_only_without_external_or_trading_surfaces() -> None:
    tree = ast.parse(MODULE_PATH.read_text())
    forbidden_import_roots = {
        "http",
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "psycopg",
        "psycopg2",
        "sqlalchemy",
        "supabase",
        "web3",
    }
    forbidden_call_names = {
        "connect",
        "execute",
        "open",
        "request",
        "send",
        "urlopen",
        "write",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_import_roots
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                assert function.id not in forbidden_call_names
            elif isinstance(function, ast.Attribute):
                assert function.attr not in forbidden_call_names
