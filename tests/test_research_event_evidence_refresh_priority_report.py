from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def api() -> Any:
    return importlib.import_module(
        "polymarket_alpha_lab.research_event_evidence_refresh_priority_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "fresh_age_seconds": d("3600.000000"),
        "stale_age_seconds": d("7200.000000"),
        "min_source_reliability_score": d("0.700000"),
        "critical_source_reliability_score": d("0.500000"),
        "catalyst_pressure_watch_threshold": d("0.500000"),
        "catalyst_pressure_block_threshold": d("0.800000"),
        "contradiction_watch_threshold": d("1.000000"),
        "contradiction_block_threshold": d("3.000000"),
        "deadline_near_seconds": d("86400.000000"),
        "deadline_imminent_seconds": d("7200.000000"),
    }
    values.update(overrides)
    return module.ResearchEventEvidenceRefreshPriorityConfig(**values)


def evidence(
    event_domain: str,
    *,
    observed_seconds_ago: int = 600,
    source_reliability_score: Decimal = d("0.900000"),
    catalyst_pressure_score: Decimal = d("0.100000"),
    contradiction_count: Decimal = d("0.000000"),
    deadline_seconds: Decimal = d("172800.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventEvidenceRefreshPriorityInput(
        event_domain=event_domain,
        evidence_observed_at=GENERATED_AT - timedelta(seconds=observed_seconds_ago),
        source_reliability_score=source_reliability_score,
        catalyst_pressure_score=catalyst_pressure_score,
        contradiction_count=contradiction_count,
        deadline_seconds=deadline_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*rows: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_evidence_refresh_priority_report(
        rows,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_is_pass_readonly_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchEventEvidenceRefreshPriorityReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.domain_count == d("0.000000")
    assert report.evidence_count == d("0.000000")
    assert report.pass_domain_count == d("0.000000")
    assert report.watch_domain_count == d("0.000000")
    assert report.block_domain_count == d("0.000000")
    assert report.oldest_average_evidence_age_seconds == d("0.000000")
    assert report.lowest_source_reliability_score == d("0.000000")
    assert report.highest_catalyst_pressure_score == d("0.000000")
    assert report.contradiction_count == d("0.000000")
    assert report.nearest_deadline_seconds == d("0.000000")
    assert report.reason_codes == ("research_event_evidence_refresh_priority_empty",)
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_report_prioritizes_by_domain_age_reliability_catalysts_conflicts_deadline() -> None:
    report = build_report(
        evidence(
            "politics",
            observed_seconds_ago=10800,
            source_reliability_score=d("0.400000"),
            catalyst_pressure_score=d("0.850000"),
            contradiction_count=d("2.000000"),
            deadline_seconds=d("3600.000000"),
        ),
        evidence(
            "politics",
            observed_seconds_ago=7200,
            source_reliability_score=d("0.600000"),
            catalyst_pressure_score=d("0.700000"),
            contradiction_count=d("1.000000"),
            deadline_seconds=d("7200.000000"),
        ),
        evidence(
            "finance.crypto.btc",
            observed_seconds_ago=5400,
            source_reliability_score=d("0.800000"),
            catalyst_pressure_score=d("0.600000"),
            contradiction_count=d("1.000000"),
            deadline_seconds=d("36000.000000"),
        ),
        evidence(
            "finance.crypto.btc",
            observed_seconds_ago=1800,
            source_reliability_score=d("0.700000"),
            catalyst_pressure_score=d("0.300000"),
            contradiction_count=d("0.000000"),
            deadline_seconds=d("90000.000000"),
        ),
        evidence("sports.soccer"),
    )

    assert report.status == "block"
    assert report.domain_count == d("3.000000")
    assert report.evidence_count == d("5.000000")
    assert report.pass_domain_count == d("1.000000")
    assert report.watch_domain_count == d("1.000000")
    assert report.block_domain_count == d("1.000000")
    assert report.oldest_average_evidence_age_seconds == d("9000.000000")
    assert report.lowest_source_reliability_score == d("0.500000")
    assert report.highest_catalyst_pressure_score == d("0.850000")
    assert report.contradiction_count == d("4.000000")
    assert report.nearest_deadline_seconds == d("3600.000000")
    assert report.reason_codes == (
        "event_evidence_age_block",
        "source_reliability_block",
        "catalyst_pressure_block",
        "contradiction_pressure_block",
        "deadline_imminent",
        "catalyst_pressure_watch",
        "contradiction_pressure_watch",
        "deadline_near",
    )

    assert tuple(row.event_domain for row in report.rows) == (
        "politics",
        "finance.crypto.btc",
        "sports.soccer",
    )

    blocked = report.rows[0]
    assert blocked.status == "block"
    assert blocked.evidence_count == d("2.000000")
    assert blocked.average_evidence_age_seconds == d("9000.000000")
    assert blocked.max_evidence_age_seconds == d("10800.000000")
    assert blocked.average_source_reliability_score == d("0.500000")
    assert blocked.catalyst_pressure_score == d("0.850000")
    assert blocked.contradiction_count == d("3.000000")
    assert blocked.nearest_deadline_seconds == d("3600.000000")
    assert blocked.refresh_priority_score == d("0.858333")
    assert blocked.reason_codes == (
        "event_evidence_age_block",
        "source_reliability_block",
        "catalyst_pressure_block",
        "contradiction_pressure_block",
        "deadline_imminent",
    )

    watch = report.rows[1]
    assert watch.status == "watch"
    assert watch.average_evidence_age_seconds == d("3600.000000")
    assert watch.average_source_reliability_score == d("0.750000")
    assert watch.refresh_priority_score == d("0.450000")
    assert watch.reason_codes == (
        "catalyst_pressure_watch",
        "contradiction_pressure_watch",
        "deadline_near",
    )

    passed = report.rows[2]
    assert passed.status == "pass"
    assert passed.refresh_priority_score == d("0.065833")
    assert passed.reason_codes == ("event_evidence_refresh_current",)


def test_payload_and_digest_are_deterministic_json_ready_and_identifier_safe() -> None:
    module = api()
    report_a = build_report(
        evidence(
            "finance.crypto.btc",
            observed_seconds_ago=5400,
            source_reliability_score=d("0.800000"),
            catalyst_pressure_score=d("0.600000"),
            contradiction_count=d("1.000000"),
            deadline_seconds=d("36000.000000"),
        ),
        evidence("politics", observed_seconds_ago=10800),
    )
    report_b = build_report(
        evidence("politics", observed_seconds_ago=10800),
        evidence(
            "finance.crypto.btc",
            observed_seconds_ago=5400,
            source_reliability_score=d("0.800000"),
            catalyst_pressure_score=d("0.600000"),
            contradiction_count=d("1.000000"),
            deadline_seconds=d("36000.000000"),
        ),
    )

    payload_a = module.research_event_evidence_refresh_priority_report_payload(report_a)
    payload_b = module.research_event_evidence_refresh_priority_report_payload(report_b)
    digest_a = module.research_event_evidence_refresh_priority_report_digest(report_a)
    digest_b = module.research_event_evidence_refresh_priority_report_digest(report_b)

    assert payload_a == payload_b
    assert digest_a == digest_b
    assert len(digest_a) == 64
    int(digest_a, 16)
    assert payload_a["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload_a["domain_count"] == "2.000000"
    assert payload_a["rows"][0]["refresh_priority_score"] >= payload_a["rows"][1][
        "refresh_priority_score"
    ]
    json.dumps(payload_a, sort_keys=True)
    assert_no_float_values(payload_a)

    keys = {field.name for cls in (type(report_a), type(report_a.rows[0])) for field in fields(cls)}
    assert {
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "event_identifier",
        "source_identifier",
        "reference",
        "url",
    }.isdisjoint(keys)


def test_validation_rejects_public_numeric_non_decimals_dates_flags_and_statuses() -> None:
    module = api()

    with pytest.raises(ValueError, match="fresh_age_seconds must be a Decimal"):
        config(fresh_age_seconds=_DecimalSubclass("3600.000000"))
    with pytest.raises(ValueError, match="source_reliability_score must be a Decimal"):
        evidence("politics", source_reliability_score=0.8)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="contradiction_count must be a Decimal"):
        evidence("politics", contradiction_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="deadline_seconds must be positive"):
        evidence("politics", deadline_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="event_domain contains unsafe text"):
        evidence("finance.crypto.btc/event-secret")
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        module.build_research_event_evidence_refresh_priority_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must be timezone-aware"):
        module.ResearchEventEvidenceRefreshPriorityInput(
            event_domain="politics",
            evidence_observed_at=datetime(2026, 7, 2, 11, 0),
            source_reliability_score=d("0.900000"),
            catalyst_pressure_score=d("0.100000"),
            contradiction_count=d("0.000000"),
            deadline_seconds=d("172800.000000"),
        )
    with pytest.raises(ValueError, match="evidence_observed_at must not be in the future"):
        build_report(evidence("politics", observed_seconds_ago=-1))
    with pytest.raises(ValueError, match="paper_only"):
        evidence("politics", paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        evidence("politics", report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        evidence("politics", readonly=False)

    report = build_report(evidence("politics"))
    with pytest.raises(ValueError, match="status"):
        replace(report, status="clear")
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")


def test_exports_frozen_dataclasses_and_status_vocabulary() -> None:
    module = api()
    report = build_report(evidence("politics"))

    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_REPORT_CONFIG_VERSION",
        "RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_STATUSES",
        "ResearchEventEvidenceRefreshPriorityConfig",
        "ResearchEventEvidenceRefreshPriorityInput",
        "ResearchEventEvidenceRefreshPriorityReport",
        "ResearchEventEvidenceRefreshPriorityRow",
        "build_research_event_evidence_refresh_priority_report",
        "research_event_evidence_refresh_priority_report_digest",
        "research_event_evidence_refresh_priority_report_payload",
    )
    assert module.RESEARCH_EVENT_EVIDENCE_REFRESH_PRIORITY_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert is_dataclass(config())
    assert is_dataclass(evidence("sports.soccer"))
    assert is_dataclass(report)
    assert is_dataclass(report.rows[0])

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "block"
    with pytest.raises(FrozenInstanceError):
        config().fresh_age_seconds = d("1.000000")


def test_module_scope_is_pure_public_safe_report_only() -> None:
    module = api()
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    lowered = source.lower()
    for forbidden in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "private_key",
        "credential",
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


def assert_no_float_values(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_values(item)
    elif isinstance(value, list):
        for item in value:
            assert_no_float_values(item)
    else:
        assert type(value) is not float
