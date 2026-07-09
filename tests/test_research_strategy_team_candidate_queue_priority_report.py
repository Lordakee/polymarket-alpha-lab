from __future__ import annotations

import ast
import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_team_candidate_queue_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _join(*parts: str) -> str:
    return "".join(parts)


def canonical_digest(payload: dict[str, Any]) -> str:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest")
    encoded = json.dumps(unsigned, sort_keys=True, separators=(",", ":")).encode()
    return hashlib.sha256(encoded).hexdigest()


def config(**overrides: object):
    module = api()
    return module.ResearchStrategyTeamCandidateQueuePriorityConfig(**overrides)


def queue_item(
    queue_key: str,
    *,
    team_bucket: str = "macro",
    candidate_bucket: str = "event_resolution",
    queued_at: datetime = datetime(2026, 7, 9, 11, 30, tzinfo=UTC),
    last_reviewed_at: datetime | None = GENERATED_AT,
    evidence_completeness_score: Decimal = d("0.950000"),
    source_freshness_score: Decimal = d("0.950000"),
    team_coverage_score: Decimal = d("0.950000"),
    resolution_learning_score: Decimal = d("0.200000"),
    review_load_score: Decimal = d("0.100000"),
):
    module = api()
    return module.ResearchStrategyTeamCandidateQueuePriorityInput(
        queue_key=queue_key,
        team_bucket=team_bucket,
        candidate_bucket=candidate_bucket,
        queued_at=queued_at,
        last_reviewed_at=last_reviewed_at,
        evidence_completeness_score=evidence_completeness_score,
        source_freshness_score=source_freshness_score,
        team_coverage_score=team_coverage_score,
        resolution_learning_score=resolution_learning_score,
        review_load_score=review_load_score,
    )


def build_report(*items, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_team_candidate_queue_priority_report(
        items,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_queue_priority_report_prioritizes_rows_and_builds_public_digest() -> None:
    items = (
        queue_item("raw-private-pass-candidate-001"),
        queue_item(
            "raw-private-block-candidate-002",
            team_bucket="weather",
            candidate_bucket="forecast_update",
            queued_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
            last_reviewed_at=datetime(2026, 7, 6, 12, 0, tzinfo=UTC),
            evidence_completeness_score=d("0.400000"),
            source_freshness_score=d("0.300000"),
            team_coverage_score=d("0.500000"),
            resolution_learning_score=d("0.900000"),
            review_load_score=d("0.850000"),
        ),
        queue_item(
            "raw-private-watch-candidate-003",
            team_bucket="sports",
            candidate_bucket="score_review",
            queued_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            last_reviewed_at=datetime(2026, 7, 8, 11, 0, tzinfo=UTC),
            evidence_completeness_score=d("0.700000"),
            source_freshness_score=d("0.700000"),
            team_coverage_score=d("0.750000"),
            resolution_learning_score=d("0.400000"),
            review_load_score=d("0.500000"),
        ),
    )

    report = build_report(*items)
    reversed_report = build_report(*reversed(items))

    assert report.status == "block"
    assert tuple(row.queue_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert tuple(row.status for row in report.rows) == ("block", "watch", "pass")
    assert report.queue_item_count == d("3")
    assert report.block_count == d("1")
    assert report.watch_count == d("1")
    assert report.pass_count == d("1")
    assert report.max_queue_priority_score == d("1.000000")
    assert report.max_queue_age_seconds == d("259200.000000")
    assert report.max_review_load_score == d("0.850000")
    assert report.mean_resolution_learning_score == d("0.500000")

    blocked = report.rows[0]
    assert blocked.queue_priority_score == d("1.000000")
    assert blocked.queue_age_seconds == d("259200.000000")
    assert blocked.reason_codes == (
        "team_candidate_queue_priority_evidence_completeness_block",
        "team_candidate_queue_priority_source_freshness_block",
        "team_candidate_queue_priority_team_coverage_block",
        "team_candidate_queue_priority_queue_age_block",
        "team_candidate_queue_priority_review_load_block",
    )
    assert report.rows[1].reason_codes == (
        "team_candidate_queue_priority_evidence_completeness_watch",
        "team_candidate_queue_priority_source_freshness_watch",
        "team_candidate_queue_priority_team_coverage_watch",
        "team_candidate_queue_priority_queue_age_watch",
        "team_candidate_queue_priority_review_load_watch",
    )
    assert report.rows[2].reason_codes == ("team_candidate_queue_priority_clear",)

    payload = api().research_strategy_team_candidate_queue_priority_report_payload(report)
    reversed_payload = api().research_strategy_team_candidate_queue_priority_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["rows"][0]["queue_priority_score"] == "1.000000"
    assert payload["rows"][0]["queue_age_seconds"] == "259200.000000"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)

    public_blob = json.dumps(payload, sort_keys=True)
    for raw_key in (
        "raw-private-pass-candidate-001",
        "raw-private-block-candidate-002",
        "raw-private-watch-candidate-003",
    ):
        assert raw_key not in public_blob
    assert _unsafe_public_key_paths(payload) == ()


def test_queue_priority_report_enforces_report_only_shape_and_guards() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_TEAM_CANDIDATE_QUEUE_PRIORITY_REPORT_CONFIG_VERSION",
        "STATUSES",
        "ResearchStrategyTeamCandidateQueuePriorityConfig",
        "ResearchStrategyTeamCandidateQueuePriorityInput",
        "ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount",
        "ResearchStrategyTeamCandidateQueuePriorityReport",
        "ResearchStrategyTeamCandidateQueuePriorityRow",
        "build_research_strategy_team_candidate_queue_priority_report",
        "research_strategy_team_candidate_queue_priority_report_digest",
        "research_strategy_team_candidate_queue_priority_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(queue_item("private-public-scope-check"))
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.rows[0].paper_only is True
    assert report.rows[0].report_only is True
    assert report.rows[0].readonly is True

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="review_load_score must be a Decimal"):
        queue_item("candidate-float", review_load_score=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="queued_at must be UTC-aware"):
        queue_item("candidate-naive", queued_at=datetime(2026, 7, 9, 10, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            queue_item("candidate-zone"),
            generated_at=datetime(
                2026,
                7,
                9,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="queue_key values must be unique"):
        build_report(queue_item("candidate-dup"), queue_item("candidate-dup"))
    with pytest.raises(ValueError, match="last_reviewed_at must not be before queued_at"):
        queue_item(
            "candidate-time",
            queued_at=datetime(2026, 7, 9, 10, 0, tzinfo=UTC),
            last_reviewed_at=datetime(2026, 7, 9, 9, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="evidence_completeness_pass_floor"):
        config(
            evidence_completeness_pass_floor=d("0.500000"),
            evidence_completeness_block_floor=d("0.600000"),
        )
    with pytest.raises(ValueError, match="supported diagnostics"):
        module.ResearchStrategyTeamCandidateQueuePriorityRow(
            queue_rank=d("1"),
            public_candidate_digest="a" * 64,
            team_bucket="macro",
            candidate_bucket="event_resolution",
            status="pass",
            queue_priority_score=d("0"),
            queue_age_seconds=d("0"),
            evidence_completeness_score=d("1"),
            source_freshness_score=d("1"),
            team_coverage_score=d("1"),
            resolution_learning_score=d("0"),
            review_load_score=d("0"),
            reason_codes=("team_candidate_queue_priority_unmodeled",),
        )
    with pytest.raises(ValueError, match="supported diagnostics"):
        module.ResearchStrategyTeamCandidateQueuePriorityReasonCodeCount(
            reason_code="team_candidate_queue_priority_unmodeled",
            count=d("1"),
        )

    empty = build_report()
    assert empty.status == "pass"
    assert empty.reason_codes == ("team_candidate_queue_priority_empty",)
    assert empty.queue_item_count == d("0")
    assert empty.rows == ()

    payload = module.research_strategy_team_candidate_queue_priority_report_payload(report)
    assert module.research_strategy_team_candidate_queue_priority_report_digest(report) == (
        payload["derived_validation_digest"]
    )
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True

    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        _join("reco", "mmendation"),
        _join("siz", "ing"),
        _join("b", "uy"),
        _join("s", "ell"),
        _join("wal", "let"),
        _join("ord", "er"),
        _join("li", "ve"),
        _join("trad", "ing"),
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def _float_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    if isinstance(value, float):
        return (prefix or "<root>",)
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_float_paths(nested, child))
        return tuple(paths)
    return ()


def _unsafe_public_key_paths(value: object, prefix: str = "") -> tuple[str, ...]:
    unsafe_terms = (
        _join("raw", "_candidate", "_id"),
        _join("queue", "_key"),
        _join("mar", "ket", "_id"),
        _join("mar", "ket", "_sl", "ug"),
        _join("ques", "tion"),
        _join("sou", "rce", "_u", "rl"),
        _join("sou", "rce", "_te", "xt"),
        _join("d", "sn"),
        _join("ta", "ble", "_na", "me"),
        _join("to", "ken"),
        _join("wal", "let"),
        _join("ord", "er"),
        _join("tra", "de"),
        _join("tra", "ding"),
    )
    if isinstance(value, dict):
        paths: list[str] = []
        for key, nested in value.items():
            child = str(key) if not prefix else f"{prefix}.{key}"
            if any(term in str(key).lower() for term in unsafe_terms):
                paths.append(child)
            paths.extend(_unsafe_public_key_paths(nested, child))
        return tuple(paths)
    if isinstance(value, list | tuple):
        paths = []
        for index, nested in enumerate(value):
            child = str(index) if not prefix else f"{prefix}.{index}"
            paths.extend(_unsafe_public_key_paths(nested, child))
        return tuple(paths)
    return ()
