from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest


GENERATED_AT = datetime(2026, 7, 9, 15, 0, tzinfo=UTC)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_evidence_source_latency_gate_report.py"
)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DateTimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_evidence_source_latency_gate_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _input(
    evidence_ref: str,
    channel_label: str,
    *,
    available_at: datetime,
    checked_at: datetime | None,
    reliability_score: Decimal,
    confirmation_count: Decimal,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.ResearchStrategyEvidenceSourceLatencyGateInput(
        evidence_ref=evidence_ref,
        channel_label=channel_label,
        available_at=available_at,
        checked_at=checked_at,
        reliability_score=reliability_score,
        confirmation_count=confirmation_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object):
    module = api()
    return module.ResearchStrategyEvidenceSourceLatencyGateConfig(**overrides)


def _build_report(*items, config=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_evidence_source_latency_gate_report(
        items,
        config=_config() if config is None else config,
        generated_at=generated_at,
    )


def test_latency_gate_aggregates_sanitized_public_channel_rows() -> None:
    module = api()
    passing = _input(
        "private-pass-ref",
        "official_feed",
        available_at=GENERATED_AT - timedelta(minutes=10),
        checked_at=GENERATED_AT - timedelta(minutes=5),
        reliability_score=d("0.900000"),
        confirmation_count=d("3.000000"),
    )
    watched = _input(
        "private-watch-ref",
        "expert_notes",
        available_at=GENERATED_AT - timedelta(minutes=30),
        checked_at=GENERATED_AT - timedelta(minutes=10),
        reliability_score=d("0.550000"),
        confirmation_count=ONE,
    )
    blocked = _input(
        "private-block-ref",
        "filing_feed",
        available_at=GENERATED_AT - timedelta(hours=2),
        checked_at=None,
        reliability_score=d("0.200000"),
        confirmation_count=ZERO,
    )

    report = _build_report(passing, watched, blocked)
    permuted = _build_report(blocked, passing, watched)
    payload = module.research_strategy_evidence_source_latency_gate_report_payload(report)

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.evidence_count == d("3.000000")
    assert report.channel_count == d("3.000000")
    assert report.pass_count == ONE
    assert report.watch_count == ONE
    assert report.block_count == ONE
    assert report.missing_check_count == ONE
    assert report.average_latency_seconds == d("750.000000")
    assert report.max_latency_seconds == d("1200.000000")
    assert report.min_reliability_score == d("0.200000")
    assert report.public_payload_digest == (
        module.research_strategy_evidence_source_latency_gate_digest(report)
    )

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    blocked_row, watched_row, passing_row = report.rows
    assert blocked_row.rank == ONE
    assert blocked_row.channel_label == "filing_feed"
    assert blocked_row.sample_count == ONE
    assert blocked_row.checked_count == ZERO
    assert blocked_row.missing_check_count == ONE
    assert blocked_row.average_latency_seconds == ZERO
    assert blocked_row.max_latency_seconds == ZERO
    assert blocked_row.min_reliability_score == d("0.200000")
    assert blocked_row.min_confirmation_count == ZERO
    assert blocked_row.reason_codes == (
        "evidence_source_latency_gate_block",
        "missing_evidence_check",
        "reliability_below_block_threshold",
        "confirmation_count_zero",
    )
    assert watched_row.status == "watch"
    assert watched_row.average_latency_seconds == d("1200.000000")
    assert watched_row.reason_codes == (
        "evidence_source_latency_gate_watch",
        "latency_above_watch_threshold",
        "confirmation_count_below_minimum",
    )
    assert passing_row.status == "pass"
    assert passing_row.average_latency_seconds == d("300.000000")
    assert passing_row.reason_codes == ("evidence_source_latency_gate_pass",)

    assert payload == module.research_strategy_evidence_source_latency_gate_report_payload(
        permuted,
    )
    assert payload["public_payload_digest"] == report.public_payload_digest
    assert payload["rows"][0]["public_payload_digest"] == blocked_row.public_payload_digest
    assert payload["rows"][1]["average_latency_seconds"] == "1200.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert _number_paths(payload) == ()
    encoded = json.dumps(payload, sort_keys=True).lower()
    for forbidden in (
        "private-pass-ref",
        "private-watch-ref",
        "private-block-ref",
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
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
    ):
        assert forbidden not in encoded


def test_empty_latency_gate_report_blocks_without_private_refs() -> None:
    module = api()
    generated_at = datetime(2026, 7, 9, 11, 0, tzinfo=timezone(timedelta(hours=-4)))

    report = _build_report(generated_at=generated_at)
    payload = module.research_strategy_evidence_source_latency_gate_report_payload(report)

    assert report.generated_at == GENERATED_AT
    assert report.status == "block"
    assert report.evidence_count == ZERO
    assert report.channel_count == ZERO
    assert report.pass_count == ZERO
    assert report.watch_count == ZERO
    assert report.block_count == ZERO
    assert report.missing_check_count == ZERO
    assert report.average_latency_seconds == ZERO
    assert report.max_latency_seconds == ZERO
    assert report.min_reliability_score == ZERO
    assert report.rows == ()
    assert report.reason_codes == ("evidence_source_latency_gate_missing_inputs",)
    assert payload["generated_at"] == "2026-07-09T15:00:00+00:00"
    assert payload["rows"] == []
    assert payload["public_payload_digest"] == report.public_payload_digest


def test_decimal_only_frozen_flags_and_strict_validation() -> None:
    module = api()
    report = _build_report(
        _input(
            "private-frozen",
            "public_channel",
            available_at=GENERATED_AT - timedelta(minutes=2),
            checked_at=GENERATED_AT - timedelta(minutes=1),
            reliability_score=d("0.800000"),
            confirmation_count=d("2.000000"),
        ),
    )

    for instance in (
        _config(),
        report,
        report.rows[0],
    ):
        assert is_dataclass(instance)
        for field in fields(instance):
            value = getattr(instance, field.name)
            if isinstance(value, Decimal):
                assert type(value) is Decimal
            assert type(value) is not int
            assert type(value) is not float

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        _input(
            "private-flag",
            "public_channel",
            available_at=GENERATED_AT - timedelta(minutes=2),
            checked_at=GENERATED_AT - timedelta(minutes=1),
            reliability_score=d("0.800000"),
            confirmation_count=d("2.000000"),
            paper_only=False,
        )
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="reliability_score must be a Decimal"):
        _input(
            "private-int",
            "public_channel",
            available_at=GENERATED_AT - timedelta(minutes=2),
            checked_at=GENERATED_AT - timedelta(minutes=1),
            reliability_score=1,  # type: ignore[arg-type]
            confirmation_count=d("2.000000"),
        )
    with pytest.raises(ValueError, match="confirmation_count must be a Decimal"):
        _input(
            "private-subclass",
            "public_channel",
            available_at=GENERATED_AT - timedelta(minutes=2),
            checked_at=GENERATED_AT - timedelta(minutes=1),
            reliability_score=d("0.800000"),
            confirmation_count=_DecimalSubclass("2.000000"),
        )
    with pytest.raises(ValueError, match="evidence_ref values must be unique"):
        duplicate = _input(
            "private-duplicate",
            "public_channel",
            available_at=GENERATED_AT - timedelta(minutes=2),
            checked_at=GENERATED_AT - timedelta(minutes=1),
            reliability_score=d("0.800000"),
            confirmation_count=d("2.000000"),
        )
        _build_report(duplicate, duplicate)
    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        module.build_research_strategy_evidence_source_latency_gate_report(
            (),
            generated_at=_DateTimeSubclass(2026, 7, 9, 15, 0, tzinfo=UTC),
        )

    class _NoneOffsetTz(tzinfo):
        def utcoffset(self, dt):
            return None

        def dst(self, dt):
            return None

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_evidence_source_latency_gate_report(
            (),
            generated_at=datetime(2026, 7, 9, 15, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="latency_block_seconds"):
        _config(latency_block_seconds=d("900.000000"))
    with pytest.raises(ValueError, match="reliability_watch_threshold"):
        _config(
            reliability_watch_threshold=d("0.200000"),
            reliability_block_threshold=d("0.250000"),
        )
    with pytest.raises(ValueError, match="status must be pass, watch, or block"):
        replace(report, status="blocked")


def test_public_digest_and_payload_validation_reject_tampering() -> None:
    module = api()
    item = _input(
        "private-consistent",
        "public_channel",
        available_at=GENERATED_AT - timedelta(minutes=2),
        checked_at=GENERATED_AT - timedelta(minutes=1),
        reliability_score=d("0.800000"),
        confirmation_count=d("2.000000"),
    )
    report = _build_report(item)
    payload = module.research_strategy_evidence_source_latency_gate_report_payload(report)

    assert module.research_strategy_evidence_source_latency_gate_report_payload(payload) == payload
    assert module.research_strategy_evidence_source_latency_gate_digest_payload(report)[
        "public_payload_digest"
    ] is None

    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(
            report.rows[0],
            average_latency_seconds=report.rows[0].average_latency_seconds + ONE,
        )
    with pytest.raises(ValueError, match="public_payload_digest"):
        replace(report, pass_count=d("2.000000"))
    with pytest.raises(ValueError, match="public_payload_digest"):
        module.research_strategy_evidence_source_latency_gate_report_payload(
            {**payload, "pass_count": "2.000000"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        module.research_strategy_evidence_source_latency_gate_report_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_evidence_source_latency_gate_report_payload(
            {**payload, "candidate" "_" "id": "private-consistent"},
        )
    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_evidence_source_latency_gate_report_payload(
            {**payload, "source_text": "hidden text"},
        )
    with pytest.raises(ValueError, match="Decimal string"):
        module.research_strategy_evidence_source_latency_gate_report_payload(
            {**payload, "pass_count": 1},
        )


def test_public_exports_and_static_report_only_surface() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_EVIDENCE_SOURCE_LATENCY_GATE_REPORT_CONFIG_VERSION",
        "ResearchStrategyEvidenceSourceLatencyGateConfig",
        "ResearchStrategyEvidenceSourceLatencyGateInput",
        "ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount",
        "ResearchStrategyEvidenceSourceLatencyGateReport",
        "ResearchStrategyEvidenceSourceLatencyGateRow",
        "build_research_strategy_evidence_source_latency_gate_report",
        "research_strategy_evidence_source_latency_gate_digest",
        "research_strategy_evidence_source_latency_gate_digest_payload",
        "research_strategy_evidence_source_latency_gate_report_payload",
    )

    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source_text.lower()
    tree = ast.parse(source_text)
    public_forbidden = (
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
        "order",
        "trade",
        "buy",
        "sell",
        "recommend",
        "sizing",
        "database",
        "network",
        "auth",
        "live",
    )
    runtime_forbidden = {
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
    forbidden_calls = {
        "connect",
        "delete",
        "execute",
        "insert",
        "login",
        "open",
        "post",
        "request",
        "submit",
        "update",
        "urlopen",
        "write",
    }

    for forbidden in public_forbidden:
        assert forbidden not in lowered
    for public_name in module.__all__:
        lowered_name = public_name.lower()
        assert not any(term in lowered_name for term in public_forbidden)
    for cls in (
        module.ResearchStrategyEvidenceSourceLatencyGateConfig,
        module.ResearchStrategyEvidenceSourceLatencyGateInput,
        module.ResearchStrategyEvidenceSourceLatencyGateRow,
        module.ResearchStrategyEvidenceSourceLatencyGateReasonCodeCount,
        module.ResearchStrategyEvidenceSourceLatencyGateReport,
    ):
        for field in fields(cls):
            lowered_name = field.name.lower()
            assert not any(term in lowered_name for term in public_forbidden)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & runtime_forbidden)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in runtime_forbidden
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in forbidden_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in forbidden_calls


def _number_paths(value: object, path: str = "") -> tuple[str, ...]:
    if type(value) in (float, int, Decimal):
        return (path or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, item in value.items():
            paths.extend(_number_paths(item, f"{path}.{key}" if path else str(key)))
        return tuple(paths)
    if isinstance(value, list):
        paths = []
        for index, item in enumerate(value):
            paths.extend(_number_paths(item, f"{path}[{index}]"))
        return tuple(paths)
    return ()
