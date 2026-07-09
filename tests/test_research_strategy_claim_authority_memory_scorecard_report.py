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


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_strategy_claim_authority_memory_scorecard_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_strategy_claim_authority_memory_scorecard_report.py"
)
GENERATED_AT = datetime(2026, 7, 9, 16, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 15, 30, tzinfo=UTC)


class DecimalSubclass(Decimal):
    pass


class DateTimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def cfg(module: Any, **overrides: object) -> Any:
    values = {
        "config_version": (
            module.DEFAULT_RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_REPORT_CONFIG_VERSION
        ),
        "pass_min_score": d("0.800000"),
        "watch_min_score": d("0.600000"),
        "min_pass_claim_authority_score": d("0.800000"),
        "min_watch_claim_authority_score": d("0.600000"),
        "min_pass_memory_recall_score": d("0.750000"),
        "min_watch_memory_recall_score": d("0.550000"),
        "min_pass_evidence_alignment_score": d("0.700000"),
        "min_watch_evidence_alignment_score": d("0.550000"),
        "max_pass_conflict_score": d("0.200000"),
        "max_watch_conflict_score": d("0.450000"),
        "claim_authority_weight": d("0.350000"),
        "memory_recall_weight": d("0.300000"),
        "evidence_alignment_weight": d("0.200000"),
        "conflict_safety_weight": d("0.150000"),
    }
    values.update(overrides)
    return module.ResearchStrategyClaimAuthorityMemoryScorecardConfig(**values)


def signal(
    module: Any,
    index: int,
    *,
    claim_group: str | None = None,
    claim_authority_score: Decimal = d("0.950000"),
    memory_recall_score: Decimal = d("0.900000"),
    evidence_alignment_score: Decimal = d("0.850000"),
    conflict_score: Decimal = d("0.100000"),
    observed_at: datetime = OBSERVED_AT,
    reason_codes: tuple[str, ...] = ("memory_trace_ready",),
) -> Any:
    return module.ResearchStrategyClaimAuthorityMemoryScorecardInput(
        claim_group=claim_group or f"group-{index:03d}",
        private_candidate_reference=(
            f"candidate=CAND-{index:03d}; token=secret; wallet=0xabc"
        ),
        private_market_reference=(
            f"market_slug=hidden-{index}; market_question=Will Alpha resolve?"
        ),
        private_source_reference=(
            f"source_url=https://source.example/private/{index}; "
            f"source_text=private evidence; dsn=postgres://secret; "
            f"table=claim_memory"
        ),
        observed_at=observed_at,
        claim_authority_score=claim_authority_score,
        memory_recall_score=memory_recall_score,
        evidence_alignment_score=evidence_alignment_score,
        conflict_score=conflict_score,
        reason_codes=reason_codes,
    )


def build_report(module: Any, rows: tuple[Any, ...], **overrides: object) -> Any:
    values = {
        "signals": rows,
        "generated_at": GENERATED_AT,
        "config": cfg(module),
    }
    values.update(overrides)
    return module.build_research_strategy_claim_authority_memory_scorecard_report(
        **values,
    )


def payload(module: Any, report: Any) -> dict[str, Any]:
    return module.research_strategy_claim_authority_memory_scorecard_report_public_payload(
        report,
    )


def digest(module: Any, report: Any) -> str:
    return module.research_strategy_claim_authority_memory_scorecard_report_digest(
        report,
    )


def validate(module: Any, value: Any) -> dict[str, Any]:
    return (
        module.validate_research_strategy_claim_authority_memory_scorecard_report_public_payload(
            value,
        )
    )


def unsigned_digest(public_payload: dict[str, Any]) -> str:
    unsigned = dict(public_payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, ensure_ascii=True, separators=(",", ":"), sort_keys=True)
    return hashlib.sha256(encoded.encode("utf-8")).hexdigest()


def test_builds_claim_authority_memory_scorecard_without_private_payload_leaks() -> None:
    module = api()
    report = build_report(
        module,
        (
            signal(module, 1, claim_group="group-pass"),
            signal(
                module,
                2,
                claim_group="group-watch",
                claim_authority_score=d("0.700000"),
                memory_recall_score=d("0.650000"),
                evidence_alignment_score=d("0.750000"),
                conflict_score=d("0.350000"),
                reason_codes=("human_review_flagged",),
            ),
            signal(
                module,
                3,
                claim_group="group-block",
                claim_authority_score=d("0.450000"),
                memory_recall_score=d("0.400000"),
                evidence_alignment_score=d("0.500000"),
                conflict_score=d("0.800000"),
                reason_codes=("missing_memory_trace",),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert type(report) is module.ResearchStrategyClaimAuthorityMemoryScorecardReport
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        "research-strategy-claim-authority-memory-scorecard-report-v0"
    )
    assert report.status == "block"
    assert report.signal_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.average_score == d("0.667500")
    assert report.weakest_score == d("0.407500")
    assert report.highest_conflict_score == d("0.800000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    block_row, watch_row, pass_row = report.rows
    assert block_row.rank == d("1.000000")
    assert block_row.claim_group == "group-block"
    assert block_row.claim_digest.startswith("sha256:")
    assert block_row.context_digest.startswith("sha256:")
    assert block_row.evidence_digest.startswith("sha256:")
    assert block_row.score == d("0.407500")
    assert block_row.conflict_safety_score == d("0.200000")
    assert block_row.reason_codes == (
        "missing_memory_trace",
        "claim_authority_block",
        "memory_recall_block",
        "evidence_alignment_block",
        "conflict_pressure_block",
        "aggregate_score_block",
    )
    assert watch_row.score == d("0.687500")
    assert watch_row.reason_codes == (
        "human_review_flagged",
        "claim_authority_watch",
        "memory_recall_watch",
        "conflict_pressure_watch",
        "aggregate_score_watch",
    )
    assert pass_row.score == d("0.907500")
    assert pass_row.reason_codes == ("memory_trace_ready", "claim_authority_memory_pass")

    public_payload = payload(module, report)
    encoded_payload = json.dumps(public_payload, sort_keys=True).lower()
    forbidden_private_terms = (
        "candidate=cand-",
        "market_slug",
        "market_question",
        "will alpha resolve",
        "source_url",
        "source_text",
        "https://source.example",
        "dsn=postgres",
        "claim_memory",
        "token=secret",
        "wallet=0xabc",
        "private_candidate_reference",
        "private_market_reference",
        "private_source_reference",
    )
    assert all(term not in encoded_payload for term in forbidden_private_terms)
    assert public_payload["rows"][0]["claim_digest"].startswith("sha256:")
    assert public_payload["rows"][0]["score"] == "0.407500"


def test_public_payload_is_deterministic_decimal_stringed_and_digest_validated() -> None:
    module = api()
    first = build_report(
        module,
        (
            signal(module, 2, claim_group="group-watch", claim_authority_score=d("0.700000")),
            signal(module, 1, claim_group="group-pass"),
        ),
    )
    second = build_report(
        module,
        (
            signal(module, 1, claim_group="group-pass"),
            signal(module, 2, claim_group="group-watch", claim_authority_score=d("0.700000")),
        ),
    )

    first_payload = payload(module, first)
    second_payload = payload(module, second)

    assert first_payload == second_payload
    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.derived_validation_digest == digest(module, first)
    assert first_payload["derived_validation_digest"] == unsigned_digest(first_payload)
    assert validate(module, first_payload) == first_payload
    assert len(first.derived_validation_digest) == 64
    int(first.derived_validation_digest, 16)
    assert first_payload["generated_at"] == "2026-07-09T16:00:00+00:00"
    assert first_payload["signal_count"] == "2.000000"
    assert first_payload["rows"][0]["observed_at"] == "2026-07-09T15:30:00+00:00"
    assert not any(type(value) in (int, float) for value in walk_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in walk_values(first_payload))

    tampered_digest = dict(first_payload)
    tampered_digest["derived_validation_digest"] = "0" * 64
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate(module, tampered_digest)

    tampered_score = json.loads(json.dumps(first_payload))
    tampered_score["rows"][0]["score"] = "0.010000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate(module, tampered_score)

    bad_flag = json.loads(json.dumps(first_payload))
    bad_flag["rows"][0]["readonly"] = False
    bad_flag["derived_validation_digest"] = unsigned_digest(bad_flag)
    with pytest.raises(ValueError, match="readonly"):
        validate(module, bad_flag)

    with pytest.raises(ValueError, match="unsafe"):
        validate(
            module,
            {
                "candidate_id": "private-alpha",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "derived_validation_digest": "0" * 64,
            },
        )

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)


def test_dataclasses_are_frozen_decimal_only_and_status_limited() -> None:
    module = api()
    sample_config = cfg(module)
    sample_input = signal(module, 1)
    sample_report = build_report(module, (sample_input,))
    sample_row = sample_report.rows[0]
    sample_reason_count = sample_report.reason_code_counts[0]

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type) and exported_name.startswith("ResearchStrategy"):
            assert is_dataclass(exported)

    for item in (sample_config, sample_input, sample_row, sample_reason_count, sample_report):
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        assert_public_numeric_values_are_decimal(item)
        with pytest.raises(FrozenInstanceError):
            item.paper_only = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="claim_authority_score must be a Decimal"):
        signal(module, 1, claim_authority_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="memory_recall_score must be a Decimal"):
        signal(module, 1, memory_recall_score=DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        signal(module, 1, observed_at=DateTimeSubclass(2026, 7, 9, 15, 30, tzinfo=UTC))  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="paper_only"):
        replace(sample_report, paper_only=False)
    with pytest.raises(ValueError, match="status"):
        replace(sample_row, status="ready")
    with pytest.raises(ValueError, match="reason_codes"):
        signal(module, 1, reason_codes=("Needs Review",))

    assert module.RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_STATUSES == (
        "pass",
        "watch",
        "block",
    )


def test_public_api_and_source_stay_report_only() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_REPORT_CONFIG_VERSION",
        "RESEARCH_STRATEGY_CLAIM_AUTHORITY_MEMORY_SCORECARD_STATUSES",
        "ResearchStrategyClaimAuthorityMemoryScorecardConfig",
        "ResearchStrategyClaimAuthorityMemoryScorecardInput",
        "ResearchStrategyClaimAuthorityMemoryScorecardReasonCodeCount",
        "ResearchStrategyClaimAuthorityMemoryScorecardReport",
        "ResearchStrategyClaimAuthorityMemoryScorecardRow",
        "build_research_strategy_claim_authority_memory_scorecard_report",
        "research_strategy_claim_authority_memory_scorecard_report_digest",
        "research_strategy_claim_authority_memory_scorecard_report_public_payload",
        "validate_research_strategy_claim_authority_memory_scorecard_report_public_payload",
    )

    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()
    forbidden_runtime_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "web3",
        "wallet",
        "database",
        "network",
        "order",
        "live trading",
        "sizing",
        "recommendation",
        "auth_token",
    )
    assert all(term not in lowered for term in forbidden_runtime_terms)

    tree = ast.parse(source)
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in {
                "float",
                "open",
                "connect",
                "request",
                "post",
                "get",
                "send",
                "submit",
                "cancel",
            }


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        values: list[Any] = []
        for item in value.values():
            values.extend(walk_values(item))
        return tuple(values)
    if isinstance(value, list):
        values = []
        for item in value:
            values.extend(walk_values(item))
        return tuple(values)
    return (value,)


def assert_public_numeric_values_are_decimal(value: object) -> None:
    if type(value) is bool or value is None:
        return
    if type(value) is Decimal:
        return
    if type(value) in (int, float):
        raise AssertionError(f"public numeric value must be Decimal, got {value!r}")
    if is_dataclass(value) and not isinstance(value, type):
        for field in fields(value):
            assert_public_numeric_values_are_decimal(getattr(value, field.name))
        return
    if isinstance(value, (tuple, list)):
        for item in value:
            assert_public_numeric_values_are_decimal(item)
