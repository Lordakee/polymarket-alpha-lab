from __future__ import annotations

import ast
import hashlib
import importlib.util
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from importlib import import_module
from pathlib import Path
from typing import Any, get_type_hints

import pytest


MODULE_NAME = "polymarket_alpha_lab.research_strategy_execution_readiness_safety_report"
SOURCE = Path(
    "src/polymarket_alpha_lab/research_strategy_execution_readiness_safety_report.py",
)
GENERATED_AT = datetime(2026, 7, 8, 14, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _api() -> Any:
    return import_module(MODULE_NAME)


def _at(**kwargs: int) -> datetime:
    return GENERATED_AT - timedelta(**kwargs)


def _config(**overrides: object) -> object:
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_STRATEGY_EXECUTION_READINESS_SAFETY_REPORT_CONFIG_VERSION
        ),
        "min_research_quality_score": d("0.800000"),
        "min_source_independence_score": d("0.750000"),
        "min_resolution_clarity_score": d("0.800000"),
        "min_liquidity_review_score": d("0.700000"),
        "min_risk_control_score": d("0.800000"),
        "min_edge_quality_score": d("0.010000"),
        "watch_margin": d("0.050000"),
        "max_research_age_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return api.ResearchStrategyExecutionReadinessSafetyConfig(**values)


def _candidate(
    public_candidate_ref: str,
    *,
    research_packet_ref: str = "packet-public-alpha",
    evaluated_at: datetime | None = None,
    research_quality_score: Decimal = Decimal("0.900000"),
    source_independence_score: Decimal = Decimal("0.850000"),
    resolution_clarity_score: Decimal = Decimal("0.900000"),
    liquidity_review_score: Decimal = Decimal("0.800000"),
    risk_control_score: Decimal = Decimal("0.900000"),
    edge_quality_score: Decimal = Decimal("0.025000"),
    public_evidence_redacted: bool = True,
    research_packet_complete: bool = True,
) -> object:
    api = _api()
    return api.ResearchStrategyExecutionReadinessSafetyCandidate(
        public_candidate_ref=public_candidate_ref,
        research_packet_ref=research_packet_ref,
        evaluated_at=evaluated_at or _at(hours=2),
        research_quality_score=research_quality_score,
        source_independence_score=source_independence_score,
        resolution_clarity_score=resolution_clarity_score,
        liquidity_review_score=liquidity_review_score,
        risk_control_score=risk_control_score,
        edge_quality_score=edge_quality_score,
        public_evidence_redacted=public_evidence_redacted,
        research_packet_complete=research_packet_complete,
    )


def _report(*candidates: object, **config_overrides: object) -> object:
    api = _api()
    return api.build_research_strategy_execution_readiness_safety_report(
        candidates,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_report_rolls_up_pass_watch_block_rows_with_public_flags_and_digest() -> None:
    api = _api()
    report = _report(
        _candidate(
            "research-pass",
            research_packet_ref="packet-pass",
            evaluated_at=_at(hours=1),
        ),
        _candidate(
            "research-watch",
            research_packet_ref="packet-watch",
            research_quality_score=d("0.780000"),
            evaluated_at=_at(hours=3),
        ),
        _candidate(
            "research-block",
            research_packet_ref="packet-block",
            risk_control_score=d("0.600000"),
            public_evidence_redacted=False,
            evaluated_at=_at(hours=30),
        ),
    )

    assert api.READINESS_STATUSES == ("pass", "watch", "block")
    assert type(report) is api.ResearchStrategyExecutionReadinessSafetyReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.report_status == "block"
    assert report.candidate_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.pass_ratio == d("0.333333")
    assert report.blocking_finding_count == d("3.000000")
    assert report.watch_finding_count == d("1.000000")
    assert report.max_research_age_seconds == d("108000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert len(report.public_payload_digest) == 64
    assert report.public_payload_digest == report.public_payload_digest.lower()

    assert tuple(row.public_candidate_ref for row in report.rows) == (
        "research-block",
        "research-watch",
        "research-pass",
    )
    blocked = report.rows[0]
    assert blocked.readiness_status == "block"
    assert blocked.research_age_seconds == d("108000.000000")
    assert blocked.finding_count == d("3.000000")
    assert blocked.reason_codes == (
        "research_strategy_execution_readiness_safety_public_redaction_gap",
        "research_strategy_execution_readiness_safety_research_stale",
        "research_strategy_execution_readiness_safety_risk_control_block",
    )

    watched = report.rows[1]
    assert watched.readiness_status == "watch"
    assert watched.finding_count == d("1.000000")
    assert watched.reason_codes == (
        "research_strategy_execution_readiness_safety_research_quality_watch",
    )

    passed = report.rows[2]
    assert passed.readiness_status == "pass"
    assert passed.finding_count == d("0.000000")
    assert passed.reason_codes == (
        "research_strategy_execution_readiness_safety_pass",
    )


def test_payload_is_deterministic_decimal_stringed_utc_digest_checked_and_leak_free() -> None:
    api = _api()
    first = _report(
        _candidate(
            "research-beta",
            research_packet_ref="packet-beta",
            evaluated_at=_at(minutes=90).astimezone(timezone(timedelta(hours=-7))),
        ),
        _candidate(
            "research-alpha",
            research_packet_ref="packet-alpha",
            evaluated_at=_at(minutes=30),
        ),
    )
    second = _report(
        _candidate(
            "research-alpha",
            research_packet_ref="packet-alpha",
            evaluated_at=_at(minutes=30),
        ),
        _candidate(
            "research-beta",
            research_packet_ref="packet-beta",
            evaluated_at=_at(minutes=90).astimezone(timezone(timedelta(hours=-7))),
        ),
    )

    first_payload = api.research_strategy_execution_readiness_safety_report_payload(first)
    second_payload = api.research_strategy_execution_readiness_safety_report_payload(second)
    encoded = json.dumps(
        {key: value for key, value in first_payload.items() if key != "public_payload_digest"},
        sort_keys=True,
        separators=(",", ":"),
    )

    assert first_payload == second_payload
    assert first.public_payload_digest == hashlib.sha256(encoded.encode("utf-8")).hexdigest()
    assert first_payload["generated_at"] == "2026-07-08T14:30:00+00:00"
    assert first_payload["candidate_count"] == "2.000000"
    assert first_payload["rows"][0]["public_candidate_ref"] == "research-alpha"
    assert first_payload["rows"][0]["research_quality_score"] == "0.900000"
    assert first_payload["rows"][1]["evaluated_at"] == "2026-07-08T13:00:00+00:00"
    assert ".0," not in repr(first_payload)

    payload_text = repr(first_payload).lower()
    forbidden_public_terms = (
        "candidate_id",
        "market_id",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "private_key",
    )
    for term in forbidden_public_terms:
        assert term not in payload_text, term


def test_rejects_floats_public_leakage_false_flags_subclasses_naive_time_and_mutation() -> None:
    api = _api()

    with pytest.raises(ValueError, match="research_quality_score must be a Decimal"):
        _candidate("research-alpha", research_quality_score=0.9)

    with pytest.raises(ValueError, match="evaluated_at must be timezone-aware"):
        _candidate("research-alpha", evaluated_at=datetime(2026, 7, 8, 12, 0))

    with pytest.raises(ValueError, match="datetime values must not be after generated_at"):
        _report(_candidate("research-alpha", evaluated_at=GENERATED_AT + timedelta(seconds=1)))

    for leaked_value in (
        "candidate_id:raw-123",
        "market_id:raw-456",
        "election-market-slug",
        "question: will this happen",
        "https://example.test/source",
        "source_text: copied feed",
        "postgres://dsn-value",
        "table_name: recommendations",
        "wallet token",
        "auth private_key",
        "order trade",
    ):
        with pytest.raises(ValueError, match="public leakage"):
            _candidate(leaked_value)

    row = _candidate("research-alpha")
    with pytest.raises(FrozenInstanceError):
        row.public_candidate_ref = "research-beta"

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(row, paper_only=False)

    with pytest.raises(ValueError, match="config must be a ResearchStrategyExecutionReadinessSafetyConfig"):
        api.build_research_strategy_execution_readiness_safety_report(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )

    class ConfigSubclass(api.ResearchStrategyExecutionReadinessSafetyConfig):
        pass

    with pytest.raises(ValueError, match="config must be a ResearchStrategyExecutionReadinessSafetyConfig"):
        api.build_research_strategy_execution_readiness_safety_report(
            (),
            config=ConfigSubclass(),
            generated_at=GENERATED_AT,
        )

    class CandidateSubclass(api.ResearchStrategyExecutionReadinessSafetyCandidate):
        pass

    with pytest.raises(ValueError, match="candidates must contain ResearchStrategyExecutionReadinessSafetyCandidate values"):
        api.build_research_strategy_execution_readiness_safety_report(
            (CandidateSubclass(public_candidate_ref="research-subclass", research_packet_ref="packet"),),
            config=_config(),
            generated_at=GENERATED_AT,
        )


def test_public_surface_decimal_annotations_statuses_and_no_side_effect_terms() -> None:
    api = _api()
    numeric_fragments = (
        "score",
        "count",
        "ratio",
        "seconds",
        "age",
        "margin",
    )

    assert api.READINESS_STATUSES == ("pass", "watch", "block")
    for cls_name in (
        "ResearchStrategyExecutionReadinessSafetyConfig",
        "ResearchStrategyExecutionReadinessSafetyCandidate",
        "ResearchStrategyExecutionReadinessSafetyRow",
        "ResearchStrategyExecutionReadinessSafetyReport",
    ):
        cls = getattr(api, cls_name)
        assert is_dataclass(cls)
        assert getattr(cls, "__dataclass_params__").frozen is True
        hints = get_type_hints(cls)
        for field in fields(cls):
            if field.name in {"paper_only", "report_only", "readonly"}:
                continue
            if any(fragment in field.name for fragment in numeric_fragments):
                assert hints[field.name] is Decimal, (cls_name, field.name, hints[field.name])

    text = SOURCE.read_text(encoding="utf-8")
    lowered = text.lower()
    forbidden_text = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "psycopg",
        "supabase",
        "sqlalchemy",
        "candidate_id",
        "market_id",
        "source_url",
        "source_text",
        "table_name",
        "private_key",
        "wallet",
        "auth",
        "order",
        "trade",
        "token",
        "open(",
        "print(",
        "connect(",
        "commit(",
        ".execute(",
    )
    for token in forbidden_text:
        assert token not in lowered, token

    allowed_import_prefixes = (
        "from __future__",
        "from dataclasses",
        "from datetime",
        "from decimal",
        "from hashlib",
        "from typing",
        "import json",
        "from polymarket_alpha_lab.team_paper_guard",
    )
    for line in text.splitlines():
        stripped = line.strip()
        if stripped.startswith("import ") or stripped.startswith("from "):
            assert any(stripped.startswith(prefix) for prefix in allowed_import_prefixes), stripped

    tree = ast.parse(text)
    forbidden_calls = {"open", "print", "exec", "eval", "compile"}
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in forbidden_calls
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr not in forbidden_calls

    assert importlib.util.find_spec(MODULE_NAME) is not None
    for name, value in inspect.getmembers(api):
        if name.startswith("_"):
            continue
        if isinstance(value, float):
            raise AssertionError(name)
