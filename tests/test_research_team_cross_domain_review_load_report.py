from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import json
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_team_cross_domain_review_load_report as subject
from polymarket_alpha_lab.research_team_cross_domain_review_load_report import (
    DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_REVIEW_LOAD_REPORT_CONFIG_VERSION,
    PUBLIC_STATUSES,
    ResearchTeamCrossDomainReviewLoadConfig,
    ResearchTeamCrossDomainReviewLoadObservation,
    ResearchTeamCrossDomainReviewLoadReport,
    build_research_team_cross_domain_review_load_report,
    format_research_team_cross_domain_review_load_digest,
    research_team_cross_domain_review_load_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_PATH = Path("src/polymarket_alpha_lab/research_team_cross_domain_review_load_report.py")
ZERO = Decimal("0.000000")


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    team_id: str,
    domain: str,
    *,
    capacity_points: Decimal = d("10.000000"),
    active_queue_points: Decimal = d("1.000000"),
    stale_memory_count: Decimal = ZERO,
    oldest_memory_age_seconds: Decimal = d("1000.000000"),
    calibration_backlog_count: Decimal = ZERO,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamCrossDomainReviewLoadObservation:
    return ResearchTeamCrossDomainReviewLoadObservation(
        team_id=team_id,
        domain=domain,
        capacity_points=capacity_points,
        active_queue_points=active_queue_points,
        stale_memory_count=stale_memory_count,
        oldest_memory_age_seconds=oldest_memory_age_seconds,
        calibration_backlog_count=calibration_backlog_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build(
    rows: tuple[ResearchTeamCrossDomainReviewLoadObservation, ...],
    *,
    generated_at: datetime = GENERATED_AT,
    config: ResearchTeamCrossDomainReviewLoadConfig | None = None,
) -> ResearchTeamCrossDomainReviewLoadReport:
    return build_research_team_cross_domain_review_load_report(
        rows,
        generated_at=generated_at,
        config=config,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if item is None:
            continue
        if isinstance(item, Decimal):
            assert type(item) is Decimal
            continue
        if field.name.endswith(("_count", "_points", "_score", "_seconds", "_pressure")):
            assert type(item) is Decimal


def test_cross_domain_review_load_reports_specialist_bottlenecks_by_domain() -> None:
    report = build(
        (
            observation("politics_review", "politics"),
            observation(
                "crypto_review",
                "crypto",
                capacity_points=d("8.000000"),
                active_queue_points=d("10.000000"),
                stale_memory_count=d("4.000000"),
                oldest_memory_age_seconds=d("172800.000000"),
                calibration_backlog_count=d("5.000000"),
            ),
            observation(
                "equities_review",
                "equities",
                active_queue_points=d("6.000000"),
                stale_memory_count=d("1.000000"),
                oldest_memory_age_seconds=d("90000.000000"),
                calibration_backlog_count=d("2.000000"),
            ),
            observation("commodities_review", "commodities"),
            observation("football_review", "football"),
            observation("basketball_review", "basketball"),
            observation("general_review", "other"),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_REVIEW_LOAD_REPORT_CONFIG_VERSION
    )
    assert subject.REVIEW_DOMAINS == (
        "politics",
        "crypto",
        "equities",
        "commodities",
        "football",
        "basketball",
        "other",
    )
    assert {row.domain for row in report.rows} == set(subject.REVIEW_DOMAINS)
    assert report.report_status == "block"
    assert report.team_count == d("7.000000")
    assert report.pass_count == d("5.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_capacity_points == d("68.000000")
    assert report.total_active_queue_points == d("21.000000")
    assert report.total_stale_memory_count == d("5.000000")
    assert report.total_calibration_backlog_count == d("7.000000")
    assert report.max_review_load_score == d("0.887500")
    assert report.average_review_load_score == d("0.230201")
    assert report.reason_codes == ("cross_domain_review_load_report_block",)
    assert report.public_digest.startswith("sha256:")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.team_id, row.domain, row.status) for row in report.rows)[:3] == (
        ("crypto_review", "crypto", "block"),
        ("equities_review", "equities", "watch"),
        ("basketball_review", "basketball", "pass"),
    )
    crypto = report.rows[0]
    assert crypto.active_queue_pressure == d("1.000000")
    assert crypto.stale_memory_pressure == d("1.000000")
    assert crypto.calibration_backlog_pressure == d("0.625000")
    assert crypto.review_load_score == d("0.887500")
    equities = report.rows[1]
    assert equities.active_queue_pressure == d("0.600000")
    assert equities.stale_memory_pressure == d("1.000000")
    assert equities.calibration_backlog_pressure == d("0.200000")
    assert equities.review_load_score == d("0.600000")

    for row in report.rows:
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True
        assert_decimal_numeric_fields(row)
    assert_decimal_numeric_fields(report)

    digest = format_research_team_cross_domain_review_load_digest(report)
    assert "status=block" in digest
    assert "active_queue_points=21.000000" in digest
    assert "stale_memory_count=5.000000" in digest
    assert "calibration_backlog_count=7.000000" in digest
    assert f"public_digest={report.public_digest}" in digest


def test_cross_domain_review_load_payload_and_digest_are_deterministic() -> None:
    rows = (
        observation(
            "equities_review",
            "equities",
            active_queue_points=d("6.000000"),
            stale_memory_count=d("1.000000"),
            oldest_memory_age_seconds=d("90000.000000"),
            calibration_backlog_count=d("2.000000"),
        ),
        observation("politics_review", "politics"),
    )

    first = build(rows)
    second = build(tuple(reversed(rows)), generated_at=GENERATED_AT)

    assert first.public_digest == second.public_digest
    assert research_team_cross_domain_review_load_payload(first) == (
        research_team_cross_domain_review_load_payload(second)
    )

    payload = research_team_cross_domain_review_load_payload(first)
    assert payload["public_digest"] == first.public_digest
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert "6.000000" in walk_values(payload)
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert research_team_cross_domain_review_load_payload(payload) == payload

    tampered = dict(payload)
    tampered["total_active_queue_points"] = "999.000000"
    with pytest.raises(ValueError, match="public_digest"):
        research_team_cross_domain_review_load_payload(tampered)


def test_cross_domain_review_load_statuses_are_exactly_pass_watch_block() -> None:
    assert PUBLIC_STATUSES == ("pass", "watch", "block")

    pass_report = build((observation("politics_review", "politics"),))
    watch_report = build(
        (
            observation(
                "equities_review",
                "equities",
                active_queue_points=d("6.000000"),
                stale_memory_count=d("1.000000"),
                oldest_memory_age_seconds=d("90000.000000"),
                calibration_backlog_count=d("2.000000"),
            ),
        ),
    )
    block_report = build(
        (
            observation(
                "crypto_review",
                "crypto",
                capacity_points=d("8.000000"),
                active_queue_points=d("10.000000"),
                stale_memory_count=d("4.000000"),
                oldest_memory_age_seconds=d("172800.000000"),
                calibration_backlog_count=d("5.000000"),
            ),
        ),
    )

    assert pass_report.report_status == "pass"
    assert watch_report.report_status == "watch"
    assert block_report.report_status == "block"


def test_cross_domain_review_load_requires_frozen_dataclasses_and_decimal_inputs() -> None:
    report = build((observation("politics_review", "politics"),))

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]

    for value in (report, report.rows[0]):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert_decimal_numeric_fields(value)

    with pytest.raises(ValueError, match="Decimal"):
        observation("politics_review", "politics", active_queue_points=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation("politics_review", "politics", stale_memory_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(
            "politics_review",
            "politics",
            capacity_points=_DecimalSubclass("10.000000"),
        )
    with pytest.raises(ValueError, match="domain"):
        observation("soccer_review", "soccer")
    with pytest.raises(ValueError, match="paper_only"):
        observation("politics_review", "politics", paper_only=False)


def test_cross_domain_review_load_dataclasses_do_not_support_subclassing() -> None:
    with pytest.raises(TypeError):

        class DerivedConfig(ResearchTeamCrossDomainReviewLoadConfig):
            pass

    with pytest.raises(TypeError):

        class DerivedObservation(ResearchTeamCrossDomainReviewLoadObservation):
            pass

    with pytest.raises(TypeError):

        class DerivedReport(ResearchTeamCrossDomainReviewLoadReport):
            pass

    with pytest.raises(TypeError):

        class DerivedRow(subject.ResearchTeamCrossDomainReviewLoadRow):
            pass


def test_cross_domain_review_load_rejects_raw_identifiers_and_unsafe_payloads() -> None:
    unsafe_names = (
        "raw_candidate_42",
        "event_id_42",
        "market_slug_alpha",
        "source_url_99",
        "https://example.test/ref",
        "wallet_trade",
    )
    for value in unsafe_names:
        with pytest.raises(ValueError):
            observation(value, "politics")

    report = build((observation("politics_review", "politics"),))
    public_json = json.dumps(research_team_cross_domain_review_load_payload(report)).lower()
    for value in unsafe_names:
        assert value.lower() not in public_json
    for field_name in fields(ResearchTeamCrossDomainReviewLoadObservation):
        assert field_name.name not in {
            "candidate_id",
            "market_id",
            "market_slug",
            "market_question",
            "source_id",
            "source_reference",
            "source_url",
            "source_text",
            "dsn",
            "table_name",
            "token",
        }

    tampered = research_team_cross_domain_review_load_payload(report)
    tampered["rows"][0]["team_id"] = "raw_candidate_42"  # type: ignore[index]
    with pytest.raises(ValueError):
        research_team_cross_domain_review_load_payload(tampered)

    tampered_key = research_team_cross_domain_review_load_payload(report)
    tampered_key["market_id"] = "public-looking"
    with pytest.raises(ValueError):
        research_team_cross_domain_review_load_payload(tampered_key)


def test_cross_domain_review_load_module_has_no_db_network_execution_or_trading_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    banned_import_roots = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "web3",
        "subprocess",
    }
    imports: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imports.update(alias.name.split(".")[0] for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module:
            imports.add(node.module.split(".")[0])
    assert imports.isdisjoint(banned_import_roots)

    banned_call_names = {
        "connect",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "send",
        "post",
        "put",
        "patch",
        "delete",
        "request",
        "place_order",
        "size_order",
        "recommend",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

    public_exports = set(getattr(subject, "__all__"))
    assert not any("order" in name or "wallet" in name or "trade" in name for name in public_exports)
    assert not any("recommend" in name or "sizing" in name or "live" in name for name in public_exports)


def test_cross_domain_review_load_rejects_mismatched_public_digest() -> None:
    report = build((observation("politics_review", "politics"),))
    values = {
        field.name: getattr(report, field.name)
        for field in fields(ResearchTeamCrossDomainReviewLoadReport)
    }
    values["public_digest"] = "sha256:" + ("0" * 64)

    with pytest.raises(ValueError, match="public_digest"):
        ResearchTeamCrossDomainReviewLoadReport(**values)
