from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
CLAIM_CAPTURED_AT = datetime(2026, 7, 9, 10, 0, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DatetimeSubclass(datetime):
    pass


class NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_source_cross_tool_claim_latency_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "watch_claim_latency_seconds": d("900.000000"),
        "block_claim_latency_seconds": d("3600.000000"),
        "minimum_pass_tool_count": d("2.000000"),
        "minimum_watch_tool_count": d("1.000000"),
        "minimum_pass_authority_score": d("0.750000"),
        "minimum_watch_authority_score": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchSourceCrossToolClaimLatencyConfig(**values)


def observation(
    claim_scope: str,
    tool_name: str,
    *,
    claim_captured_at: datetime = CLAIM_CAPTURED_AT,
    tool_claim_observed_at: datetime | None = CLAIM_CAPTURED_AT + timedelta(minutes=5),
    tool_authority_score: Decimal = d("0.900000"),
    claim_digest: str = "a" * 64,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceCrossToolClaimLatencyObservation(
        claim_scope=claim_scope,
        tool_name=tool_name,
        claim_digest=claim_digest,
        claim_captured_at=claim_captured_at,
        tool_claim_observed_at=tool_claim_observed_at,
        tool_authority_score=tool_authority_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_source_cross_tool_claim_latency_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_builds_cross_tool_claim_latency_report_with_pass_watch_and_block_rows() -> None:
    module = api()
    report = build_report(
        observation("claim-alpha", "scrapling"),
        observation("claim-alpha", "agent_reach", tool_authority_score=d("0.800000")),
        observation(
            "claim-beta",
            "browser_capture",
            tool_claim_observed_at=CLAIM_CAPTURED_AT + timedelta(minutes=20),
            tool_authority_score=d("0.600000"),
            claim_digest="b" * 64,
        ),
        observation(
            "claim-gamma",
            "fallback",
            tool_claim_observed_at=None,
            tool_authority_score=d("0.300000"),
            claim_digest="c" * 64,
        ),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.claim_scope_count == d("3.000000")
    assert report.observation_count == d("4.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.latency_issue_count == d("2.000000")
    assert report.missing_tool_claim_count == d("1.000000")
    assert report.low_authority_claim_count == d("2.000000")
    assert report.issue_ratio == d("0.666667")
    assert report.max_claim_latency_seconds == d("7200.000000")
    assert report.lowest_tool_authority_score == d("0.300000")
    assert len(report.public_digest) == 64
    int(report.public_digest, 16)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.claim_scope for row in report.rows) == (
        "claim-gamma",
        "claim-beta",
        "claim-alpha",
    )

    blocked, watched, passed = report.rows
    assert blocked.status == "block"
    assert blocked.tool_count == d("1.000000")
    assert blocked.observed_tool_count == d("0.000000")
    assert blocked.max_claim_latency_seconds == d("7200.000000")
    assert blocked.average_claim_latency_seconds == d("7200.000000")
    assert blocked.lowest_tool_authority_score == d("0.300000")
    assert blocked.reason_codes == (
        "cross_tool_claim_latency_block",
        "missing_tool_claim",
        "claim_latency_above_block_threshold",
        "authority_score_below_watch_threshold",
    )

    assert watched.status == "watch"
    assert watched.max_claim_latency_seconds == d("1200.000000")
    assert watched.average_claim_latency_seconds == d("1200.000000")
    assert watched.reason_codes == (
        "cross_tool_claim_latency_watch",
        "claim_latency_above_watch_threshold",
        "authority_score_below_pass_threshold",
        "tool_count_below_pass_threshold",
    )

    assert passed.status == "pass"
    assert passed.tool_count == d("2.000000")
    assert passed.average_claim_latency_seconds == d("300.000000")
    assert passed.reason_codes == ("cross_tool_claim_latency_pass",)

    payload = module.research_source_cross_tool_claim_latency_report_public_payload(
        report,
    )
    assert payload == report.public_payload
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["claim_scope_count"] == "3.000000"
    assert payload["rows"][0]["max_claim_latency_seconds"] == "7200.000000"
    assert payload["public_digest"] == report.public_digest
    json.dumps(payload, sort_keys=True)
    assert_no_float_or_int(payload)
    module.validate_research_source_cross_tool_claim_latency_report_public_payload(
        payload,
    )


def test_empty_and_deterministic_reports_are_pass_and_digest_stable() -> None:
    empty = build_report()
    assert empty.status == "pass"
    assert empty.claim_scope_count == d("0.000000")
    assert empty.observation_count == d("0.000000")
    assert empty.issue_ratio == d("0.000000")
    assert empty.reason_codes == ("cross_tool_claim_latency_no_inputs",)
    assert empty.rows == ()

    first_items = (
        observation("scope-b", "scrapling", claim_digest="b" * 64),
        observation("scope-a", "agent_reach", claim_digest="a" * 64),
        observation("scope-a", "browser_capture", claim_digest="a" * 64),
    )
    report = build_report(*first_items)
    same_report = build_report(*tuple(reversed(first_items)))
    changed_report = build_report(
        observation("scope-b", "scrapling", claim_digest="b" * 64),
        observation("scope-a", "agent_reach", claim_digest="a" * 64),
        observation(
            "scope-a",
            "browser_capture",
            claim_digest="a" * 64,
            tool_authority_score=d("0.800000"),
        ),
    )

    assert tuple(row.claim_scope for row in report.rows) == ("scope-b", "scope-a")
    assert report.public_digest == same_report.public_digest
    assert report.public_digest != changed_report.public_digest


def test_dataclasses_are_frozen_exact_type_decimal_only_and_reject_bad_inputs() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_REPORT_CONFIG_VERSION",
        "RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_TOOLS",
        "RESEARCH_SOURCE_CROSS_TOOL_CLAIM_LATENCY_STATUSES",
        "ResearchSourceCrossToolClaimLatencyConfig",
        "ResearchSourceCrossToolClaimLatencyObservation",
        "ResearchSourceCrossToolClaimLatencyReport",
        "ResearchSourceCrossToolClaimLatencyRow",
        "build_research_source_cross_tool_claim_latency_report",
        "research_source_cross_tool_claim_latency_report_public_digest",
        "research_source_cross_tool_claim_latency_report_public_payload",
        "validate_research_source_cross_tool_claim_latency_report_public_payload",
    )
    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)

    report = build_report(
        observation("claim-alpha", "scrapling"),
        observation("claim-alpha", "agent_reach"),
    )
    for item in (config(), observation("claim-alpha", "scrapling"), report, *report.rows):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
                or field.name.endswith("_score")
            ):
                assert value is None or type(value) is Decimal

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"  # type: ignore[misc]
    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchSourceCrossToolClaimLatencyConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(module.ResearchSourceCrossToolClaimLatencyObservation):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchSourceCrossToolClaimLatencyRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchSourceCrossToolClaimLatencyReport):
            pass

    with pytest.raises(ValueError, match="watch_claim_latency_seconds must be a Decimal"):
        config(watch_claim_latency_seconds=900)
    with pytest.raises(ValueError, match="tool_authority_score must be a Decimal"):
        observation("claim-alpha", "scrapling", tool_authority_score=DecimalSubclass("0.9"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation("claim-alpha", "scrapling", paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        config(readonly=False)
    with pytest.raises(ValueError, match="claim_captured_at must be a datetime"):
        observation(
            "claim-alpha",
            "scrapling",
            claim_captured_at=DatetimeSubclass(2026, 7, 9, 10, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="claim_captured_at must be timezone-aware"):
        observation(
            "claim-alpha",
            "scrapling",
            claim_captured_at=datetime(2026, 7, 9, 10, 0),
        )
    with pytest.raises(ValueError, match="claim_captured_at must be timezone-aware"):
        observation(
            "claim-alpha",
            "scrapling",
            claim_captured_at=datetime(2026, 7, 9, 10, 0, tzinfo=NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="tool_claim_observed_at"):
        observation(
            "claim-alpha",
            "scrapling",
            tool_claim_observed_at=CLAIM_CAPTURED_AT - timedelta(seconds=1),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_report(
            observation(
                "claim-alpha",
                "scrapling",
                tool_claim_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="duplicate"):
        build_report(
            observation("claim-alpha", "scrapling"),
            observation("claim-alpha", "scrapling"),
        )
    with pytest.raises(ValueError, match="observations"):
        module.build_research_source_cross_tool_claim_latency_report(
            "bad",
            config=config(),
            generated_at=GENERATED_AT,
        )

    shifted = build_report(
        observation(
            "claim-alpha",
            "scrapling",
            claim_captured_at=datetime(
                2026,
                7,
                9,
                6,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
            tool_claim_observed_at=datetime(
                2026,
                7,
                9,
                6,
                5,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
    )
    assert shifted.rows[0].max_claim_latency_seconds == d("300.000000")


def test_public_payload_is_sanitized_and_tamper_evident() -> None:
    module = api()
    report = build_report(
        observation("claim-alpha", "scrapling"),
        observation("claim-alpha", "agent_reach"),
    )

    payload = module.research_source_cross_tool_claim_latency_report_public_payload(
        report,
    )
    serialized = json.dumps(payload, sort_keys=True)
    for blocked_text in (
        "raw-candidate-123",
        "market-123",
        "question text",
        "https://example.com/source",
        "source text",
        "postgres://dsn",
        "private_table",
        "wallet",
        "order",
        "trade",
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    ):
        assert blocked_text not in serialized.lower()

    tampered_payload = dict(payload)
    tampered_payload["pass_count"] = "99.000000"
    with pytest.raises(ValueError, match="public_digest"):
        module.validate_research_source_cross_tool_claim_latency_report_public_payload(
            tampered_payload,
        )

    object.__setattr__(report.rows[0], "status", "block")
    with pytest.raises(ValueError, match="public_digest"):
        module.research_source_cross_tool_claim_latency_report_public_payload(report)

    with pytest.raises(ValueError, match="unsafe public surface"):
        observation("claim-alpha-slug", "scrapling")
    with pytest.raises(ValueError, match="unsafe public surface"):
        observation("claim-alpha", "scrapling", claim_digest="https://example.com/source")


def test_report_consistency_and_source_omit_forbidden_runtime_surfaces() -> None:
    module = api()
    report = build_report(
        observation("claim-alpha", "scrapling"),
        observation("claim-alpha", "agent_reach"),
    )

    with pytest.raises(ValueError, match="claim_scope_count"):
        replace(report, claim_scope_count=d("2.000000"))
    with pytest.raises(ValueError, match="pass_count"):
        replace(report, pass_count=d("0.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=(report.rows[0], report.rows[0]))
    with pytest.raises(ValueError, match="public_digest"):
        replace(report, public_digest="0" * 64)

    source = Path(
        "src/polymarket_alpha_lab/research_source_cross_tool_claim_latency_report.py",
    ).read_text(encoding="utf-8")
    lowered = source.lower()
    for blocked_text in (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "private_key",
        "credential",
        "secret",
        "signing",
        "submit",
        "cancel",
        "broker",
        "live_trading",
        "sizing",
        "recommendation",
    ):
        assert blocked_text not in lowered

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"


def assert_no_float_or_int(value: Any) -> None:
    if isinstance(value, float):
        raise AssertionError("payload must not contain floats")
    if type(value) is int:
        raise AssertionError("payload numeric values must be Decimal strings")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int(item)
