from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.domain_specialist_research_queue_health_report import (
    DEFAULT_DOMAIN_SPECIALIST_RESEARCH_QUEUE_HEALTH_REPORT_CONFIG_VERSION,
    DomainSpecialistResearchQueueHealthConfig,
    DomainSpecialistResearchQueueHealthInput,
    DomainSpecialistResearchQueueHealthReport,
    build_domain_specialist_research_queue_health_report,
    domain_specialist_research_queue_health_report_digest,
    domain_specialist_research_queue_health_report_payload,
)


ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> DomainSpecialistResearchQueueHealthConfig:
    values = {
        "config_version": DEFAULT_DOMAIN_SPECIALIST_RESEARCH_QUEUE_HEALTH_REPORT_CONFIG_VERSION,
        "minimum_pass_ready_ratio": d("0.700000"),
        "minimum_watch_ready_ratio": d("0.400000"),
        "maximum_pass_stale_ratio": d("0.100000"),
        "maximum_watch_stale_ratio": d("0.250000"),
        "maximum_pass_blocked_ratio": d("0.050000"),
        "maximum_watch_blocked_ratio": d("0.150000"),
        "maximum_pass_source_age_seconds": d("86400.000000"),
        "maximum_watch_source_age_seconds": d("259200.000000"),
        "maximum_pass_review_lag_seconds": d("43200.000000"),
        "maximum_watch_review_lag_seconds": d("172800.000000"),
        "queue_health_pass_score": d("0.800000"),
        "queue_health_watch_score": d("0.500000"),
        "ready_ratio_weight": d("0.400000"),
        "source_age_weight": d("0.200000"),
        "review_lag_weight": d("0.200000"),
        "memory_readiness_weight": d("0.100000"),
        "playbook_readiness_weight": d("0.100000"),
    }
    values.update(overrides)
    return DomainSpecialistResearchQueueHealthConfig(**values)


def queue_input(
    *,
    queued_candidate_count: Decimal = d("10"),
    stale_candidate_count: Decimal = d("0"),
    blocked_candidate_count: Decimal = d("0"),
    ready_candidate_count: Decimal = d("8"),
    average_source_age_seconds: Decimal = d("3600.000000"),
    average_review_lag_seconds: Decimal = d("7200.000000"),
    supabase_memory_ready: bool = True,
    playbook_ready: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> DomainSpecialistResearchQueueHealthInput:
    return DomainSpecialistResearchQueueHealthInput(
        queued_candidate_count=queued_candidate_count,
        stale_candidate_count=stale_candidate_count,
        blocked_candidate_count=blocked_candidate_count,
        ready_candidate_count=ready_candidate_count,
        average_source_age_seconds=average_source_age_seconds,
        average_review_lag_seconds=average_review_lag_seconds,
        supabase_memory_ready=supabase_memory_ready,
        playbook_ready=playbook_ready,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    value: DomainSpecialistResearchQueueHealthInput | None = None,
    *,
    cfg: DomainSpecialistResearchQueueHealthConfig | None = None,
) -> DomainSpecialistResearchQueueHealthReport:
    return build_domain_specialist_research_queue_health_report(
        value or queue_input(),
        config=cfg or config(),
    )


def test_queue_health_report_scores_pass_band_with_decimal_outputs() -> None:
    health_report = report()

    assert type(health_report) is DomainSpecialistResearchQueueHealthReport
    assert is_dataclass(health_report)
    assert health_report.config_version == "domain-specialist-research-queue-health-report-v0"
    assert health_report.queued_candidate_count == d("10.000000")
    assert health_report.ready_candidate_count == d("8.000000")
    assert health_report.ready_ratio == d("0.800000")
    assert health_report.queue_health_score == d("0.908889")
    assert health_report.queue_health_band == "pass"
    assert health_report.blocked_reason_codes == ()
    assert health_report.attention_reason_codes == ()
    assert health_report.paper_only is True
    assert health_report.report_only is True
    assert health_report.readonly is True


def test_queue_health_report_blocks_missing_operating_prerequisites_and_stale_backlog() -> None:
    health_report = report(
        queue_input(
            queued_candidate_count=d("20"),
            stale_candidate_count=d("7"),
            blocked_candidate_count=d("4"),
            ready_candidate_count=d("3"),
            average_source_age_seconds=d("345600.000000"),
            average_review_lag_seconds=d("259200.000000"),
            supabase_memory_ready=False,
            playbook_ready=False,
        ),
    )

    assert health_report.ready_ratio == d("0.150000")
    assert health_report.stale_ratio == d("0.350000")
    assert health_report.blocked_ratio == d("0.200000")
    assert health_report.queue_health_score == d("0.060000")
    assert health_report.queue_health_band == "block"
    assert health_report.blocked_reason_codes == (
        "ready_candidate_ratio_block",
        "stale_candidate_ratio_block",
        "blocked_candidate_ratio_block",
        "average_source_age_block",
        "average_review_lag_block",
        "supabase_memory_not_ready_block",
        "playbook_not_ready_block",
        "queue_health_score_block",
    )
    assert health_report.attention_reason_codes == ()


def test_queue_health_report_watches_midrange_backlog_without_blockers() -> None:
    health_report = report(
        queue_input(
            queued_candidate_count=d("10"),
            stale_candidate_count=d("2"),
            blocked_candidate_count=d("1"),
            ready_candidate_count=d("5"),
            average_source_age_seconds=d("129600.000000"),
            average_review_lag_seconds=d("86400.000000"),
        ),
    )

    assert health_report.ready_ratio == d("0.500000")
    assert health_report.queue_health_score == d("0.600000")
    assert health_report.queue_health_band == "watch"
    assert health_report.blocked_reason_codes == ()
    assert health_report.attention_reason_codes == (
        "ready_candidate_ratio_watch",
        "stale_candidate_ratio_watch",
        "blocked_candidate_ratio_watch",
        "average_source_age_watch",
        "average_review_lag_watch",
        "queue_health_score_watch",
    )


def test_payload_and_digest_are_deterministic_decimal_strings_and_safe() -> None:
    first = report(queue_input(queued_candidate_count=d("5"), ready_candidate_count=d("4")))
    second = report(queue_input(queued_candidate_count=d("5.000000"), ready_candidate_count=d("4.000000")))

    first_payload = domain_specialist_research_queue_health_report_payload(first)
    second_payload = domain_specialist_research_queue_health_report_payload(second)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_payload == first.public_payload
    assert domain_specialist_research_queue_health_report_digest(first) == first.digest
    assert domain_specialist_research_queue_health_report_digest(first) == (
        domain_specialist_research_queue_health_report_digest(second)
    )
    assert len(first.digest) == 64
    assert first_payload["queue_health_score"] == "0.908889"
    assert first_payload["ready_ratio"] == "0.800000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert not any(isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert ": 0." not in encoded


def test_validation_rejects_non_decimal_values_bad_flags_and_inconsistent_counts() -> None:
    populated = report()

    for value in (config(), queue_input(), populated):
        assert is_dataclass(value)
        assert value.paper_only is True
        assert value.report_only is True
        assert value.readonly is True
        for item in fields(value):
            item_value = getattr(value, item.name)
            if item.name in {
                "paper_only",
                "report_only",
                "readonly",
                "supabase_memory_ready",
                "playbook_ready",
            }:
                continue
            if item.name.endswith(("_count", "_seconds", "_ratio", "_score", "_weight")):
                assert type(item_value) is Decimal

    with pytest.raises(FrozenInstanceError):
        populated.queue_health_band = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="queued_candidate_count"):
        queue_input(queued_candidate_count=10)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="ready_candidate_count"):
        queue_input(ready_candidate_count=_DecimalSubclass("5"))
    with pytest.raises(ValueError, match="ready_candidate_count"):
        queue_input(queued_candidate_count=d("3"), ready_candidate_count=d("4"))
    with pytest.raises(ValueError, match="stale_candidate_count"):
        queue_input(stale_candidate_count=d("-1"))
    with pytest.raises(ValueError, match="supabase_memory_ready"):
        queue_input(supabase_memory_ready=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        replace(queue_input(), paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_domain_specialist_research_queue_health_report(queue_input(), config=object())  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="weights"):
        config(playbook_readiness_weight=d("0.200000"))
    with pytest.raises(ValueError, match="watch"):
        config(minimum_pass_ready_ratio=d("0.300000"))


def test_owned_module_has_no_side_effect_imports_calls_float_literals_or_execution_terms() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "domain_specialist_research_queue_health_report.py"
    )
    source = module_path.read_text(encoding="utf-8")
    text = source.lower()
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "aiohttp",
        "httpx",
        "os",
        "pathlib",
        "psycopg",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "urllib",
    }
    forbidden_calls = {
        "__import__",
        "connect",
        "execute",
        "float",
        "open",
        "request",
        "write_bytes",
        "write_text",
    }
    forbidden_terms = (
        "auth",
        "wallet",
        "order",
        "database",
        "network",
        "private-key",
        "private_key",
        "market_id",
        "market_slug",
        "condition_id",
        "token_id",
        "source_text",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    assert all(term not in text for term in forbidden_terms)


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)
