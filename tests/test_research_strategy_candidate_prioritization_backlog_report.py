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


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api():
    return importlib.import_module(
        "polymarket_alpha_lab.research_strategy_candidate_prioritization_backlog_report",
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
    return module.ResearchStrategyCandidatePrioritizationBacklogConfig(**overrides)


def packet(
    candidate_packet_id: str,
    *,
    team_id: str = "politics",
    category_id: str = "politics",
    candidate_slug: str | None = None,
    queued_at: datetime = datetime(2026, 7, 8, 10, 0, tzinfo=UTC),
    last_rechecked_at: datetime | None = GENERATED_AT,
    required_evidence_count: Decimal = d("5"),
    verified_evidence_count: Decimal = d("5"),
    source_age_seconds: Decimal = d("0.000000"),
    estimated_research_cost_units: Decimal = d("4.000000"),
    max_sane_research_cost_units: Decimal = d("10.000000"),
    required_domain_team_count: Decimal = d("3"),
    covered_domain_team_count: Decimal = d("3"),
):
    module = api()
    return module.ResearchStrategyCandidatePrioritizationBacklogInput(
        candidate_packet_id=candidate_packet_id,
        team_id=team_id,
        category_id=category_id,
        candidate_slug=candidate_slug or candidate_packet_id,
        queued_at=queued_at,
        last_rechecked_at=last_rechecked_at,
        required_evidence_count=required_evidence_count,
        verified_evidence_count=verified_evidence_count,
        source_age_seconds=source_age_seconds,
        estimated_research_cost_units=estimated_research_cost_units,
        max_sane_research_cost_units=max_sane_research_cost_units,
        required_domain_team_count=required_domain_team_count,
        covered_domain_team_count=covered_domain_team_count,
    )


def build_report(*packets, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_strategy_candidate_prioritization_backlog_report(
        packets,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_backlog_report_prioritizes_candidate_packets_and_digest_payload() -> None:
    rows = (
        packet(
            "candidate-pass",
            team_id="sports_soccer",
            category_id="sports.soccer",
        ),
        packet(
            "candidate-block",
            queued_at=datetime(2026, 7, 5, 12, 0, tzinfo=UTC),
            last_rechecked_at=datetime(2026, 7, 5, 12, 0, tzinfo=UTC),
            required_evidence_count=d("10"),
            verified_evidence_count=d("4"),
            source_age_seconds=d("259200.000000"),
            estimated_research_cost_units=d("20.000000"),
            max_sane_research_cost_units=d("10.000000"),
            required_domain_team_count=d("4"),
            covered_domain_team_count=d("1"),
        ),
        packet(
            "candidate-watch",
            team_id="crypto_btc",
            category_id="crypto.btc",
            last_rechecked_at=datetime(2026, 7, 7, 12, 0, tzinfo=UTC),
            required_evidence_count=d("10"),
            verified_evidence_count=d("8"),
            source_age_seconds=d("90000.000000"),
            estimated_research_cost_units=d("11.000000"),
            max_sane_research_cost_units=d("10.000000"),
            required_domain_team_count=d("5"),
            covered_domain_team_count=d("4"),
        ),
    )

    report = build_report(*rows)
    reversed_report = build_report(*reversed(rows))

    assert report.status == "block"
    assert tuple(row.candidate_packet_id for row in report.rows) == (
        "candidate-block",
        "candidate-watch",
        "candidate-pass",
    )
    assert tuple(row.backlog_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert report.packet_count == d("3")
    assert report.block_packet_count == d("1")
    assert report.watch_packet_count == d("1")
    assert report.pass_packet_count == d("1")
    assert report.max_backlog_priority_score == d("1.000000")
    assert report.max_evidence_gap_ratio == d("0.600000")
    assert report.max_source_age_seconds == d("259200.000000")
    assert report.max_cost_sanity_gap_ratio == d("1.000000")
    assert report.max_domain_team_coverage_gap_ratio == d("0.750000")
    assert report.max_recheck_age_seconds == d("259200.000000")

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.evidence_gap_ratio == d("0.600000")
    assert blocked.cost_sanity_gap_ratio == d("1.000000")
    assert blocked.domain_team_coverage_gap_ratio == d("0.750000")
    assert blocked.recheck_age_seconds == d("259200.000000")
    assert blocked.reason_codes == (
        "candidate_prioritization_backlog_evidence_gap_block",
        "candidate_prioritization_backlog_source_freshness_block",
        "candidate_prioritization_backlog_cost_sanity_block",
        "candidate_prioritization_backlog_domain_team_coverage_block",
        "candidate_prioritization_backlog_recheck_urgency_block",
    )

    watched = report.rows[1]
    assert watched.status == "watch"
    assert watched.evidence_gap_ratio == d("0.200000")
    assert watched.cost_sanity_gap_ratio == d("0.100000")
    assert watched.domain_team_coverage_gap_ratio == d("0.200000")
    assert watched.reason_codes == (
        "candidate_prioritization_backlog_evidence_gap_watch",
        "candidate_prioritization_backlog_source_freshness_watch",
        "candidate_prioritization_backlog_cost_sanity_watch",
        "candidate_prioritization_backlog_domain_team_coverage_watch",
        "candidate_prioritization_backlog_recheck_urgency_watch",
    )
    assert report.rows[2].status == "pass"
    assert report.rows[2].reason_codes == ("candidate_prioritization_backlog_clear",)

    payload = api().research_strategy_candidate_prioritization_backlog_report_payload(report)
    reversed_payload = api().research_strategy_candidate_prioritization_backlog_report_payload(
        reversed_report,
    )

    assert payload == reversed_payload
    assert payload["derived_validation_digest"] == canonical_digest(payload)
    assert len(payload["derived_validation_digest"]) == 64
    int(payload["derived_validation_digest"], 16)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["backlog_priority_score"] == "1.000000"
    assert payload["rows"][0]["source_age_seconds"] == "259200.000000"
    assert _float_paths(payload) == ()
    json.dumps(payload, sort_keys=True)


def test_backlog_report_validates_pure_report_only_shape_and_public_scope() -> None:
    module = api()

    assert module.__all__ == (
        "DEFAULT_RESEARCH_STRATEGY_CANDIDATE_PRIORITIZATION_BACKLOG_CONFIG_VERSION",
        "STATUSES",
        "ResearchStrategyCandidatePrioritizationBacklogConfig",
        "ResearchStrategyCandidatePrioritizationBacklogInput",
        "ResearchStrategyCandidatePrioritizationBacklogReport",
        "ResearchStrategyCandidatePrioritizationBacklogRow",
        "build_research_strategy_candidate_prioritization_backlog_report",
        "research_strategy_candidate_prioritization_backlog_report_digest",
        "research_strategy_candidate_prioritization_backlog_report_payload",
    )

    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(packet("candidate-public"))
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
    with pytest.raises(ValueError, match="source_age_seconds must be a Decimal"):
        packet("candidate-float", source_age_seconds=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="queued_at must be UTC-aware"):
        packet("candidate-naive", queued_at=datetime(2026, 7, 8, 10, 0))
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        build_report(
            packet("candidate-zone"),
            generated_at=datetime(
                2026,
                7,
                8,
                12,
                0,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        )
    with pytest.raises(ValueError, match="candidate_packet_id values must be unique"):
        build_report(packet("candidate-dup"), packet("candidate-dup"))
    with pytest.raises(ValueError, match="verified_evidence_count must not exceed"):
        packet(
            "candidate-evidence",
            required_evidence_count=d("2"),
            verified_evidence_count=d("3"),
        )
    with pytest.raises(ValueError, match="covered_domain_team_count must not exceed"):
        packet(
            "candidate-coverage",
            required_domain_team_count=d("2"),
            covered_domain_team_count=d("3"),
        )
    with pytest.raises(ValueError, match="cost_sanity_gap_block_ratio"):
        config(cost_sanity_gap_watch_ratio=d("0.500000"), cost_sanity_gap_block_ratio=d("0.100000"))

    empty = build_report()
    assert empty.status == "pass"
    assert empty.reason_codes == ("candidate_prioritization_backlog_empty",)
    assert empty.packet_count == d("0")
    assert empty.rows == ()

    payload = module.research_strategy_candidate_prioritization_backlog_report_payload(report)
    assert module.research_strategy_candidate_prioritization_backlog_report_digest(report) == (
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
