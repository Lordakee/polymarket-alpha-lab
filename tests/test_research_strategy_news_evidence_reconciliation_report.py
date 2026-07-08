from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_strategy_news_evidence_reconciliation_report"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "news_watch_age_minutes": d("60.000000"),
        "news_block_age_minutes": d("180.000000"),
        "source_class_pass_floor": d("3"),
        "source_class_block_floor": d("2"),
        "claim_consistency_watch_floor": d("0.750000"),
        "claim_consistency_block_floor": d("0.500000"),
        "contradiction_pressure_watch_threshold": d("0.250000"),
        "contradiction_pressure_block_threshold": d("0.600000"),
        "specialist_review_watch_age_minutes": d("120.000000"),
        "specialist_review_block_age_minutes": d("360.000000"),
        "manual_escalation_watch_urgency": d("0.500000"),
        "manual_escalation_block_urgency": d("0.900000"),
        "manual_escalation_window_minutes": d("120.000000"),
    }
    values.update(overrides)
    return module.ResearchStrategyNewsEvidenceReconciliationConfig(**values)


def item(**overrides: object) -> Any:
    module = api()
    values = {
        "private_candidate_reference": "candidate-alpha-secret",
        "private_market_reference": "market-alpha-private",
        "private_market_question": "Will private alpha resolve yes?",
        "private_source_reference": "https://example.test/news?token=secret-alpha",
        "private_source_text": "private source text alpha",
        "latest_news_at": GENERATED_AT - timedelta(minutes=15),
        "source_class_count": d("4"),
        "claim_count": d("6"),
        "consistent_claim_count": d("6"),
        "contradicted_claim_count": d("0"),
        "unresolved_contradiction_count": d("0"),
        "specialist_reviewed_at": GENERATED_AT - timedelta(minutes=30),
        "manual_escalation_due_at": GENERATED_AT + timedelta(minutes=480),
    }
    values.update(overrides)
    return module.ResearchStrategyNewsEvidenceReconciliationInput(**values)


def report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_strategy_news_evidence_reconciliation_report(
        items,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def assert_digest(value: str) -> None:
    assert len(value) == 64
    assert set(value) <= set("0123456789abcdef")


def assert_numeric_fields_are_decimal(value: object) -> None:
    for field in fields(value):
        nested = getattr(value, field.name)
        if type(nested) is bool:
            continue
        assert type(nested) is not float
        assert type(nested) is not int
        if isinstance(nested, tuple):
            for entry in nested:
                if is_dataclass(entry):
                    assert_numeric_fields_are_decimal(entry)


def assert_no_float_or_int_values(value: object) -> None:
    assert type(value) is not float
    assert type(value) is not int
    if isinstance(value, dict):
        for nested in value.values():
            assert_no_float_or_int_values(nested)
    elif isinstance(value, list):
        for nested in value:
            assert_no_float_or_int_values(nested)


def test_reconciliation_report_aggregates_quality_deterministically() -> None:
    result = report(
        item(
            private_candidate_reference="candidate-pass-secret",
            private_market_reference="market-pass-private",
            private_market_question="Will private pass market resolve yes?",
            private_source_reference="https://example.test/pass?token=pass-secret",
            private_source_text="private pass source text",
            latest_news_at=GENERATED_AT - timedelta(minutes=15),
            source_class_count=d("4"),
            claim_count=d("6"),
            consistent_claim_count=d("6"),
            contradicted_claim_count=d("0"),
            unresolved_contradiction_count=d("0"),
            specialist_reviewed_at=GENERATED_AT - timedelta(minutes=30),
            manual_escalation_due_at=GENERATED_AT + timedelta(minutes=480),
        ),
        item(
            private_candidate_reference="candidate-watch-secret",
            private_market_reference="market-watch-private",
            private_market_question="Will private watch market resolve no?",
            private_source_reference="https://example.test/watch?token=watch-secret",
            private_source_text="private watch source text",
            latest_news_at=GENERATED_AT - timedelta(minutes=90),
            source_class_count=d("2"),
            claim_count=d("5"),
            consistent_claim_count=d("3"),
            contradicted_claim_count=d("2"),
            unresolved_contradiction_count=d("1"),
            specialist_reviewed_at=GENERATED_AT - timedelta(minutes=180),
            manual_escalation_due_at=GENERATED_AT + timedelta(minutes=60),
        ),
        item(
            private_candidate_reference="candidate-block-secret",
            private_market_reference="market-block-private",
            private_market_question="Will private block market resolve no?",
            private_source_reference="https://example.test/block?token=block-secret",
            private_source_text="private block source text",
            latest_news_at=GENERATED_AT - timedelta(minutes=240),
            source_class_count=d("1"),
            claim_count=d("4"),
            consistent_claim_count=d("1"),
            contradicted_claim_count=d("3"),
            unresolved_contradiction_count=d("2"),
            specialist_reviewed_at=None,
            manual_escalation_due_at=GENERATED_AT - timedelta(minutes=5),
        ),
    )

    assert is_dataclass(result)
    assert result.generated_at == GENERATED_AT
    assert result.config_version == "research-strategy-news-evidence-reconciliation-v1"
    assert result.item_count == d("3")
    assert result.pass_count == d("1")
    assert result.watch_count == d("1")
    assert result.block_count == d("1")
    assert result.status == "block"
    assert result.reason_codes == (
        "news_freshness_block",
        "news_freshness_watch",
        "source_class_quorum_block",
        "source_class_quorum_watch",
        "claim_consistency_block",
        "claim_consistency_watch",
        "contradiction_pressure_block",
        "contradiction_pressure_watch",
        "specialist_review_age_block",
        "specialist_review_age_watch",
        "manual_escalation_urgency_block",
        "manual_escalation_urgency_watch",
        "news_evidence_reconciliation_pass",
    )
    assert result.paper_only is True
    assert result.report_only is True
    assert result.readonly is True
    assert_digest(result.validation_digest)
    assert_numeric_fields_are_decimal(result)

    assert tuple(row.aggregate_row_number for row in result.results) == (
        d("1"),
        d("2"),
        d("3"),
    )
    assert tuple(row.status for row in result.results) == ("block", "watch", "pass")

    blocked, watched, passed = result.results
    assert blocked.news_age_minutes == d("240.000000")
    assert blocked.news_freshness_score == d("0.000000")
    assert blocked.source_class_quorum_score == d("0.333333")
    assert blocked.claim_consistency_ratio == d("0.250000")
    assert blocked.contradiction_pressure == d("0.750000")
    assert blocked.specialist_review_age_minutes is None
    assert blocked.manual_escalation_urgency == d("1.000000")
    assert blocked.status == "block"
    assert blocked.reason_codes == (
        "news_freshness_block",
        "source_class_quorum_block",
        "claim_consistency_block",
        "contradiction_pressure_block",
        "specialist_review_age_block",
        "manual_escalation_urgency_block",
    )
    assert_digest(blocked.evidence_group_hash)
    assert_digest(blocked.source_bundle_hash)
    assert_digest(blocked.validation_digest)

    assert watched.news_age_minutes == d("90.000000")
    assert watched.news_freshness_score == d("0.500000")
    assert watched.source_class_quorum_score == d("0.666667")
    assert watched.claim_consistency_ratio == d("0.600000")
    assert watched.contradiction_pressure == d("0.400000")
    assert watched.specialist_review_age_minutes == d("180.000000")
    assert watched.manual_escalation_urgency == d("0.500000")
    assert watched.status == "watch"

    assert passed.news_age_minutes == d("15.000000")
    assert passed.news_freshness_score == d("0.916667")
    assert passed.source_class_quorum_score == d("1.000000")
    assert passed.claim_consistency_ratio == d("1.000000")
    assert passed.contradiction_pressure == d("0.000000")
    assert passed.specialist_review_age_minutes == d("30.000000")
    assert passed.manual_escalation_urgency == d("0.000000")
    assert passed.status == "pass"
    assert passed.reason_codes == ("news_evidence_reconciliation_pass",)

    same_result = report(*reversed(result_input_fixture()))
    assert same_result.validation_digest == result.validation_digest
    assert tuple(row.evidence_group_hash for row in same_result.results) == tuple(
        row.evidence_group_hash for row in result.results
    )


def result_input_fixture() -> tuple[Any, ...]:
    return (
        item(
            private_candidate_reference="candidate-pass-secret",
            private_market_reference="market-pass-private",
            private_market_question="Will private pass market resolve yes?",
            private_source_reference="https://example.test/pass?token=pass-secret",
            private_source_text="private pass source text",
            latest_news_at=GENERATED_AT - timedelta(minutes=15),
            source_class_count=d("4"),
            claim_count=d("6"),
            consistent_claim_count=d("6"),
            contradicted_claim_count=d("0"),
            unresolved_contradiction_count=d("0"),
            specialist_reviewed_at=GENERATED_AT - timedelta(minutes=30),
            manual_escalation_due_at=GENERATED_AT + timedelta(minutes=480),
        ),
        item(
            private_candidate_reference="candidate-watch-secret",
            private_market_reference="market-watch-private",
            private_market_question="Will private watch market resolve no?",
            private_source_reference="https://example.test/watch?token=watch-secret",
            private_source_text="private watch source text",
            latest_news_at=GENERATED_AT - timedelta(minutes=90),
            source_class_count=d("2"),
            claim_count=d("5"),
            consistent_claim_count=d("3"),
            contradicted_claim_count=d("2"),
            unresolved_contradiction_count=d("1"),
            specialist_reviewed_at=GENERATED_AT - timedelta(minutes=180),
            manual_escalation_due_at=GENERATED_AT + timedelta(minutes=60),
        ),
        item(
            private_candidate_reference="candidate-block-secret",
            private_market_reference="market-block-private",
            private_market_question="Will private block market resolve no?",
            private_source_reference="https://example.test/block?token=block-secret",
            private_source_text="private block source text",
            latest_news_at=GENERATED_AT - timedelta(minutes=240),
            source_class_count=d("1"),
            claim_count=d("4"),
            consistent_claim_count=d("1"),
            contradicted_claim_count=d("3"),
            unresolved_contradiction_count=d("2"),
            specialist_reviewed_at=None,
            manual_escalation_due_at=GENERATED_AT - timedelta(minutes=5),
        ),
    )


def test_payload_is_public_json_ready_and_validates_digests() -> None:
    module = api()
    result = report(*result_input_fixture())
    payload = module.research_strategy_news_evidence_reconciliation_report_payload(result)
    encoded = json.dumps(payload, sort_keys=True, allow_nan=False)

    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["item_count"] == "3"
    assert payload["results"][0]["aggregate_row_number"] == "1"
    assert payload["results"][0]["validation_digest"] == result.results[0].validation_digest
    assert payload["validation_digest"] == result.validation_digest
    assert_no_float_or_int_values(payload)
    assert module.research_strategy_news_evidence_reconciliation_report_payload(payload) == payload

    private_terms = (
        "candidate-pass-secret",
        "candidate-watch-secret",
        "candidate-block-secret",
        "market-pass-private",
        "market-watch-private",
        "market-block-private",
        "Will private",
        "https://example.test",
        "token=pass-secret",
        "private pass source text",
        "private watch source text",
        "private block source text",
        "private_candidate_reference",
        "private_market_reference",
        "private_market_question",
        "private_source_reference",
        "private_source_text",
    )
    assert [term for term in private_terms if term in encoded] == []

    with pytest.raises(ValueError, match="readonly"):
        module.research_strategy_news_evidence_reconciliation_report_payload(
            {**payload, "readonly": False},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_news_evidence_reconciliation_report_payload(
            {**payload, "source_url": "redacted"},
        )

    with pytest.raises(ValueError, match="unsafe"):
        module.research_strategy_news_evidence_reconciliation_report_payload(
            {**payload, "safe_key": "https://example.test/private?token=secret"},
        )

    with pytest.raises(ValueError, match="numeric"):
        module.research_strategy_news_evidence_reconciliation_report_payload(
            {**payload, "item_count": 3},
        )

    tampered_row = {**payload["results"][0], "news_freshness_score": "0.100000"}
    tampered_payload = {**payload, "results": [tampered_row, *payload["results"][1:]]}
    with pytest.raises(ValueError, match="validation_digest"):
        module.research_strategy_news_evidence_reconciliation_report_payload(
            tampered_payload,
        )

    with pytest.raises(ValueError, match="validation_digest"):
        module.research_strategy_news_evidence_reconciliation_report_payload(
            {**payload, "validation_digest": "0" * 64},
        )


def test_inputs_config_validation_frozen_flags_and_no_io_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="source_class_count must be a Decimal"):
        item(source_class_count=4)
    with pytest.raises(ValueError, match="claim_count must be positive"):
        item(claim_count=d("0"))
    with pytest.raises(ValueError, match="consistent_claim_count must not exceed"):
        item(claim_count=d("2"), consistent_claim_count=d("3"))
    with pytest.raises(ValueError, match="contradicted_claim_count must not exceed"):
        item(
            claim_count=d("2"),
            consistent_claim_count=d("0"),
            contradicted_claim_count=d("3"),
        )
    with pytest.raises(ValueError, match="unresolved_contradiction_count must not exceed"):
        item(contradicted_claim_count=d("1"), unresolved_contradiction_count=d("2"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        item(paper_only=False)
    with pytest.raises(ValueError, match="news watch age must not exceed"):
        config(news_watch_age_minutes=d("200.000000"), news_block_age_minutes=d("100.000000"))
    with pytest.raises(ValueError, match="source_class_block_floor must not exceed"):
        config(source_class_block_floor=d("4"), source_class_pass_floor=d("3"))
    with pytest.raises(ValueError, match="claim consistency block floor must not exceed"):
        config(
            claim_consistency_block_floor=d("0.800000"),
            claim_consistency_watch_floor=d("0.700000"),
        )
    with pytest.raises(ValueError, match="contradiction watch threshold must not exceed"):
        config(
            contradiction_pressure_watch_threshold=d("0.700000"),
            contradiction_pressure_block_threshold=d("0.600000"),
        )
    with pytest.raises(ValueError, match="manual escalation watch urgency must not exceed"):
        config(
            manual_escalation_watch_urgency=d("0.950000"),
            manual_escalation_block_urgency=d("0.900000"),
        )

    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_news_evidence_reconciliation_report(
            (item(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_strategy_news_evidence_reconciliation_report(
            (item(),),
            config=config(),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="latest_news_at must not be after generated_at"):
        report(item(latest_news_at=GENERATED_AT + timedelta(minutes=1)))
    with pytest.raises(ValueError, match="specialist_reviewed_at must not be after generated_at"):
        report(item(specialist_reviewed_at=GENERATED_AT + timedelta(minutes=1)))
    with pytest.raises(ValueError, match="input fingerprints must be unique"):
        report(item(), item())

    result = report(item())
    with pytest.raises(FrozenInstanceError):
        result.results[0].status = "block"
    with pytest.raises(ValueError, match="reconciliation_quality_score must match"):
        replace(
            result.results[0],
            reconciliation_quality_score=d("0.000000"),
        )
    with pytest.raises(ValueError, match="results must be sorted deterministically"):
        replace(
            result,
            results=(
                result.results[0],
                replace(result.results[0], aggregate_row_number=d("2")),
            ),
        )

    path = Path(
        "src/polymarket_alpha_lab/"
        "research_strategy_news_evidence_reconciliation_report.py",
    )
    tree = ast.parse(path.read_text(encoding="utf-8"))
    source = path.read_text(encoding="utf-8").lower()

    banned_imports = {
        "asyncio",
        "http",
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
    forbidden_terms = (
        "auth",
        "broker",
        "database",
        "db write",
        "live trading",
        "network",
        "order",
        "recommendation",
        "sizing",
        "supabase",
        "wallet",
    )

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            assert not ({alias.name.split(".")[0] for alias in node.names} & banned_imports)
        elif isinstance(node, ast.ImportFrom):
            assert (node.module or "").split(".")[0] not in banned_imports
        elif isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id not in banned_calls
        elif isinstance(node, ast.Attribute):
            assert node.attr not in banned_attributes

    assert [term for term in forbidden_terms if term in source] == []
