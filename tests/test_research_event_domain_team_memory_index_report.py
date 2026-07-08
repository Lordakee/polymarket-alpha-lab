from __future__ import annotations

import ast
import json
from dataclasses import FrozenInstanceError, asdict, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_domain_team_memory_index_report import (
    DEFAULT_RESEARCH_EVENT_DOMAIN_TEAM_MEMORY_INDEX_REPORT_CONFIG_VERSION,
    PUBLIC_STATUSES,
    ResearchEventDomainTeamMemoryIndexConfig,
    ResearchEventDomainTeamMemoryIndexObservation,
    ResearchEventDomainTeamMemoryIndexReport,
    build_research_event_domain_team_memory_index_report,
    research_event_domain_team_memory_index_report_digest,
    research_event_domain_team_memory_index_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object) -> ResearchEventDomainTeamMemoryIndexConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_DOMAIN_TEAM_MEMORY_INDEX_REPORT_CONFIG_VERSION
        ),
        "stale_after_seconds": d("7776000.000000"),
        "block_stale_after_seconds": d("15552000.000000"),
        "min_pass_team_count": d("2.000000"),
        "min_pass_coverage_ratio": d("0.750000"),
        "min_strong_memory_score": d("0.800000"),
        "min_watch_memory_score": d("0.500000"),
    }
    values.update(overrides)
    return ResearchEventDomainTeamMemoryIndexConfig(**values)


def _observation(
    event_domain: str,
    event_subdomain: str,
    team_key: str,
    *,
    memory_updated_at: datetime | None = None,
    memory_strength_score: Decimal = d("0.900000"),
    long_term_memory_count: Decimal = d("3.000000"),
    covered_event_count: Decimal = d("8.000000"),
    total_event_count: Decimal = d("10.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventDomainTeamMemoryIndexObservation:
    return ResearchEventDomainTeamMemoryIndexObservation(
        event_domain=event_domain,
        event_subdomain=event_subdomain,
        team_key=team_key,
        memory_updated_at=memory_updated_at or GENERATED_AT - timedelta(days=10),
        memory_strength_score=memory_strength_score,
        long_term_memory_count=long_term_memory_count,
        covered_event_count=covered_event_count,
        total_event_count=total_event_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _walk(value: object) -> tuple[object, ...]:
    if isinstance(value, dict):
        return tuple(item for nested in value.values() for item in _walk(nested))
    if isinstance(value, list):
        return tuple(item for nested in value for item in _walk(nested))
    return (value,)


def test_domain_team_memory_index_summarizes_pass_watch_and_block_subdomains() -> None:
    report = build_research_event_domain_team_memory_index_report(
        (
            _observation("politics", "election-calendar", "policy-team"),
            _observation("politics", "election-calendar", "legal-team"),
            _observation(
                "finance",
                "rates",
                "macro-team",
                memory_updated_at=GENERATED_AT - timedelta(days=120),
                memory_strength_score=d("0.700000"),
                covered_event_count=d("6.000000"),
                total_event_count=d("10.000000"),
            ),
            _observation(
                "finance",
                "rates",
                "policy-team",
                memory_updated_at=GENERATED_AT - timedelta(days=20),
                memory_strength_score=d("0.600000"),
                covered_event_count=d("7.000000"),
                total_event_count=d("10.000000"),
            ),
            _observation(
                "sports",
                "soccer",
                "sports-team",
                memory_updated_at=GENERATED_AT - timedelta(days=220),
                memory_strength_score=d("0.300000"),
                long_term_memory_count=d("1.000000"),
                covered_event_count=d("2.000000"),
                total_event_count=d("10.000000"),
            ),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert isinstance(report, ResearchEventDomainTeamMemoryIndexReport)
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == (
        DEFAULT_RESEARCH_EVENT_DOMAIN_TEAM_MEMORY_INDEX_REPORT_CONFIG_VERSION
    )
    assert report.public_status == "block"
    assert report.domain_count == d("3.000000")
    assert report.subdomain_count == d("3.000000")
    assert report.team_domain_pair_count == d("5.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.strong_memory_subdomain_count == d("1.000000")
    assert report.stale_memory_subdomain_count == d("2.000000")
    assert report.average_coverage_ratio == d("0.550000")
    assert report.average_memory_strength_score == d("0.616667")
    assert report.max_oldest_memory_age_seconds == d("19008000.000000")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple(row.public_status for row in report.rows) == (
        "block",
        "watch",
        "pass",
    )

    blocked, watched, passed = report.rows
    assert blocked.event_domain == "sports"
    assert blocked.event_subdomain == "soccer"
    assert blocked.team_count == d("1.000000")
    assert blocked.coverage_ratio == d("0.200000")
    assert blocked.average_memory_strength_score == d("0.300000")
    assert blocked.oldest_memory_age_seconds == d("19008000.000000")
    assert blocked.reason_codes == (
        "research_event_domain_team_memory_index_block_stale_memory",
        "research_event_domain_team_memory_index_low_team_coverage",
        "research_event_domain_team_memory_index_coverage_gap",
        "research_event_domain_team_memory_index_weak_memory",
    )

    assert watched.event_domain == "finance"
    assert watched.event_subdomain == "rates"
    assert watched.team_count == d("2.000000")
    assert watched.coverage_ratio == d("0.650000")
    assert watched.average_memory_strength_score == d("0.650000")
    assert watched.oldest_memory_age_seconds == d("10368000.000000")
    assert watched.reason_codes == (
        "research_event_domain_team_memory_index_stale_memory",
        "research_event_domain_team_memory_index_coverage_gap",
    )

    assert passed.event_domain == "politics"
    assert passed.event_subdomain == "election-calendar"
    assert passed.team_count == d("2.000000")
    assert passed.coverage_ratio == d("0.800000")
    assert passed.average_memory_strength_score == d("0.900000")
    assert passed.reason_codes == (
        "research_event_domain_team_memory_index_strong_memory",
    )
    assert passed.validation_digest.startswith("sha256:")

    assert report.reason_codes == (
        "research_event_domain_team_memory_index_report_block_present",
        "research_event_domain_team_memory_index_report_stale_present",
        "research_event_domain_team_memory_index_report_coverage_gap_present",
        "research_event_domain_team_memory_index_report_weak_memory_present",
        "research_event_domain_team_memory_index_report_strong_memory_present",
    )
    assert report.validation_digest.startswith("sha256:")


def test_domain_team_memory_index_has_exact_public_statuses_and_empty_report_blocks() -> None:
    assert PUBLIC_STATUSES == ("pass", "watch", "block")

    report = build_research_event_domain_team_memory_index_report(
        (),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    assert report.public_status == "block"
    assert report.domain_count == d("0.000000")
    assert report.subdomain_count == d("0.000000")
    assert report.team_domain_pair_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_event_domain_team_memory_index_report_no_inputs",
    )


def test_domain_team_memory_index_uses_frozen_dataclasses_and_hard_flags() -> None:
    obs = _observation("politics", "election-calendar", "policy-team")
    with pytest.raises(FrozenInstanceError):
        obs.team_key = "other-team"  # type: ignore[misc]

    report = build_research_event_domain_team_memory_index_report(
        (obs,),
        config=_config(min_pass_team_count=d("1.000000")),
        generated_at=GENERATED_AT,
    )
    with pytest.raises(FrozenInstanceError):
        report.public_status = "watch"  # type: ignore[misc]

    with pytest.raises(ValueError, match="paper_only"):
        replace(obs, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        _config(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(obs, readonly=False)


def test_domain_team_memory_index_rejects_non_decimal_inputs_and_invalid_types() -> None:
    with pytest.raises(ValueError, match="memory_strength_score"):
        _observation("politics", "election-calendar", "policy-team", memory_strength_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="long_term_memory_count"):
        _observation("politics", "election-calendar", "policy-team", long_term_memory_count=3)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_pass_team_count"):
        _config(min_pass_team_count=2)
    with pytest.raises(ValueError, match="min_strong_memory_score"):
        _config(min_strong_memory_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="event_domain"):
        _observation(_StringSubclass("politics"), "election-calendar", "policy-team")
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_domain_team_memory_index_report(
            (),
            config=_config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="covered_event_count"):
        _observation(
            "politics",
            "election-calendar",
            "policy-team",
            covered_event_count=d("11.000000"),
            total_event_count=d("10.000000"),
        )


def test_domain_team_memory_index_payload_is_public_safe_and_has_no_raw_detail() -> None:
    with pytest.raises(ValueError, match="event_domain"):
        _observation("market-politics", "election-calendar", "policy-team")
    with pytest.raises(ValueError, match="event_subdomain"):
        _observation("politics", "source-url", "policy-team")
    with pytest.raises(ValueError, match="team_key"):
        _observation("politics", "election-calendar", "wallet-team")

    report = build_research_event_domain_team_memory_index_report(
        (
            _observation("politics", "election-calendar", "policy-team"),
            _observation("politics", "election-calendar", "legal-team"),
        ),
        config=_config(),
        generated_at=GENERATED_AT,
    )

    public = repr(asdict(report)).lower()
    for token in (
        "candidate",
        "market",
        "slug",
        "question",
        "source",
        "url",
        "dsn",
        "table",
        "token",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
        "position",
        "buy",
        "sell",
        "recommend",
    ):
        assert token not in public

    payload = research_event_domain_team_memory_index_report_payload(report)
    payload["wallet_address"] = "0xabc"
    with pytest.raises(ValueError, match="unsafe"):
        research_event_domain_team_memory_index_report_payload(payload)


def test_domain_team_memory_index_payload_and_digest_are_deterministic() -> None:
    rows = (
        _observation("politics", "election-calendar", "policy-team"),
        _observation("politics", "election-calendar", "legal-team"),
        _observation(
            "finance",
            "rates",
            "macro-team",
            memory_updated_at=GENERATED_AT - timedelta(days=120),
            memory_strength_score=d("0.700000"),
            covered_event_count=d("6.000000"),
            total_event_count=d("10.000000"),
        ),
        _observation(
            "finance",
            "rates",
            "policy-team",
            memory_updated_at=GENERATED_AT - timedelta(days=20),
            memory_strength_score=d("0.600000"),
            covered_event_count=d("7.000000"),
            total_event_count=d("10.000000"),
        ),
    )
    first = build_research_event_domain_team_memory_index_report(
        rows,
        config=_config(),
        generated_at=GENERATED_AT,
    )
    second = build_research_event_domain_team_memory_index_report(
        tuple(reversed(rows)),
        config=_config(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-7))),
    )

    first_payload = research_event_domain_team_memory_index_report_payload(first)
    second_payload = research_event_domain_team_memory_index_report_payload(second)
    assert first_payload == second_payload
    assert json.dumps(first_payload, sort_keys=True, separators=(",", ":")) == json.dumps(
        second_payload,
        sort_keys=True,
        separators=(",", ":"),
    )
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["public_status"] == "watch"
    assert first_payload["subdomain_count"] == "2.000000"
    assert first_payload["average_coverage_ratio"] == "0.725000"
    assert first_payload["average_memory_strength_score"] == "0.775000"
    assert first_payload["paper_only"] is True
    assert first_payload["report_only"] is True
    assert first_payload["readonly"] is True
    assert [row["event_subdomain"] for row in first_payload["rows"]] == [
        "rates",
        "election-calendar",
    ]
    assert not any(isinstance(value, Decimal) for value in _walk(first_payload))
    assert not any(type(value) is int for value in _walk(first_payload))
    assert not any(type(value) is float for value in _walk(first_payload))

    digest = research_event_domain_team_memory_index_report_digest(first)
    assert digest == research_event_domain_team_memory_index_report_digest(first_payload)
    for key in (
        "generated_at",
        "config_version",
        "public_status",
        "domain_count",
        "subdomain_count",
        "team_domain_pair_count",
        "pass_count",
        "watch_count",
        "block_count",
        "strong_memory_subdomain_count",
        "stale_memory_subdomain_count",
        "average_coverage_ratio",
        "average_memory_strength_score",
        "max_oldest_memory_age_seconds",
        "reason_codes",
        "validation_digest",
        "paper_only",
        "report_only",
        "readonly",
    ):
        assert digest[key] == first_payload[key]

    tampered = dict(first_payload)
    tampered["public_status"] = "trade"
    with pytest.raises(ValueError, match="public_status"):
        research_event_domain_team_memory_index_report_payload(tampered)


def test_domain_team_memory_index_module_is_report_only_no_io_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_domain_team_memory_index_report.py"
    )
    tree = ast.parse(module_path.read_text(encoding="utf-8"))

    forbidden_modules = {
        "httpx",
        "requests",
        "socket",
        "sqlite3",
        "subprocess",
        "supabase",
        "urllib",
        "web3",
        "websocket",
    }
    forbidden_calls = {
        "connect",
        "create_order",
        "delete",
        "execute",
        "insert",
        "open",
        "patch",
        "post",
        "put",
        "request",
        "send",
        "submit",
        "update",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in forbidden_modules
        if isinstance(node, ast.ImportFrom) and node.module:
            assert node.module.split(".")[0] not in forbidden_modules
        if isinstance(node, ast.Call):
            call_name = ""
            if isinstance(node.func, ast.Name):
                call_name = node.func.id
            elif isinstance(node.func, ast.Attribute):
                call_name = node.func.attr
            assert call_name not in forbidden_calls
