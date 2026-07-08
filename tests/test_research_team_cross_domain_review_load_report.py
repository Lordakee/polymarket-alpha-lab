from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.research_team_cross_domain_review_load_report import (
    DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_REVIEW_LOAD_REPORT_CONFIG_VERSION,
    PUBLIC_STATUSES,
    ResearchTeamCrossDomainReviewLoadConfig,
    ResearchTeamCrossDomainReviewLoadObservation,
    ResearchTeamCrossDomainReviewLoadReport,
    ResearchTeamCrossDomainReviewLoadRow,
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
    domain_id: str,
    *,
    active_review_count: Decimal = d("1.000000"),
    active_review_points: Decimal = d("1.000000"),
    capacity_points: Decimal = d("10.000000"),
    overlap_domain_count: Decimal = d("1.000000"),
    catalyst_pressure_score: Decimal = d("0.100000"),
    evidence_age_seconds: Decimal = d("600.000000"),
    sla_remaining_seconds: Decimal = d("7200.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchTeamCrossDomainReviewLoadObservation:
    return ResearchTeamCrossDomainReviewLoadObservation(
        team_id=team_id,
        domain_id=domain_id,
        active_review_count=active_review_count,
        active_review_points=active_review_points,
        capacity_points=capacity_points,
        overlap_domain_count=overlap_domain_count,
        catalyst_pressure_score=catalyst_pressure_score,
        evidence_age_seconds=evidence_age_seconds,
        sla_remaining_seconds=sla_remaining_seconds,
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
        if field.name.endswith(("_count", "_points", "_score", "_seconds", "_ratio")):
            assert type(item) is Decimal


def test_cross_domain_review_load_summarizes_public_safe_team_pressure() -> None:
    report = build(
        (
            observation(
                "macro_review",
                "rates",
                active_review_count=d("2.000000"),
                active_review_points=d("2.000000"),
                capacity_points=d("10.000000"),
                overlap_domain_count=d("1.000000"),
                catalyst_pressure_score=d("0.100000"),
                evidence_age_seconds=d("600.000000"),
                sla_remaining_seconds=d("7200.000000"),
            ),
            observation(
                "sports_review",
                "soccer",
                active_review_count=d("5.000000"),
                active_review_points=d("7.000000"),
                capacity_points=d("10.000000"),
                overlap_domain_count=d("2.000000"),
                catalyst_pressure_score=d("0.500000"),
                evidence_age_seconds=d("3600.000000"),
                sla_remaining_seconds=d("1800.000000"),
            ),
            observation(
                "crypto_review",
                "stablecoin_policy",
                active_review_count=d("8.000000"),
                active_review_points=d("11.000000"),
                capacity_points=d("10.000000"),
                overlap_domain_count=d("4.000000"),
                catalyst_pressure_score=d("0.900000"),
                evidence_age_seconds=d("9000.000000"),
                sla_remaining_seconds=ZERO,
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.generated_at.tzinfo is UTC
    assert report.config_version == (
        DEFAULT_RESEARCH_TEAM_CROSS_DOMAIN_REVIEW_LOAD_REPORT_CONFIG_VERSION
    )
    assert report.report_status == "block"
    assert report.team_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.total_capacity_points == d("30.000000")
    assert report.total_active_review_points == d("20.000000")
    assert report.max_review_load_score == d("0.980000")
    assert report.average_review_load_score == d("0.569167")
    assert report.reason_codes == ("cross_domain_review_load_report_block",)
    assert report.public_digest.startswith("sha256:")
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    assert tuple((row.team_id, row.domain_id, row.status) for row in report.rows) == (
        ("crypto_review", "stablecoin_policy", "block"),
        ("sports_review", "soccer", "watch"),
        ("macro_review", "rates", "pass"),
    )
    assert report.rows[0].capacity_load_ratio == d("1.100000")
    assert report.rows[0].domain_overlap_pressure == d("1.000000")
    assert report.rows[0].evidence_age_pressure == d("1.000000")
    assert report.rows[0].sla_pressure == d("1.000000")
    assert report.rows[1].review_load_score == d("0.595000")
    assert report.rows[2].review_load_score == d("0.132500")

    for row in report.rows:
        assert row.paper_only is True
        assert row.report_only is True
        assert row.readonly is True
        assert_decimal_numeric_fields(row)
    assert_decimal_numeric_fields(report)

    digest = format_research_team_cross_domain_review_load_digest(report)
    assert "status=block" in digest
    assert f"public_digest={report.public_digest}" in digest


def test_cross_domain_review_load_payload_and_digest_are_deterministic() -> None:
    rows = (
        observation(
            "sports_review",
            "soccer",
            active_review_points=d("7.000000"),
            overlap_domain_count=d("2.000000"),
            catalyst_pressure_score=d("0.500000"),
            evidence_age_seconds=d("3600.000000"),
            sla_remaining_seconds=d("1800.000000"),
        ),
        observation(
            "macro_review",
            "rates",
            active_review_points=d("2.000000"),
            overlap_domain_count=d("1.000000"),
            catalyst_pressure_score=d("0.100000"),
            evidence_age_seconds=d("600.000000"),
            sla_remaining_seconds=d("7200.000000"),
        ),
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
    assert "7.000000" in walk_values(payload)
    assert all(type(value) is not Decimal for value in walk_values(payload))
    assert research_team_cross_domain_review_load_payload(payload) == payload


def test_cross_domain_review_load_statuses_are_exactly_pass_watch_block() -> None:
    assert PUBLIC_STATUSES == ("pass", "watch", "block")

    pass_report = build(
        (
            observation(
                "macro_review",
                "rates",
                active_review_points=d("1.000000"),
                catalyst_pressure_score=ZERO,
                evidence_age_seconds=ZERO,
                sla_remaining_seconds=d("7200.000000"),
            ),
        ),
    )
    watch_report = build(
        (
            observation(
                "sports_review",
                "soccer",
                active_review_points=d("7.000000"),
                catalyst_pressure_score=d("0.500000"),
                evidence_age_seconds=d("3600.000000"),
                sla_remaining_seconds=d("1800.000000"),
            ),
        ),
    )
    block_report = build(
        (
            observation(
                "crypto_review",
                "stablecoin_policy",
                active_review_points=d("11.000000"),
                overlap_domain_count=d("4.000000"),
                catalyst_pressure_score=d("0.900000"),
                evidence_age_seconds=d("9000.000000"),
                sla_remaining_seconds=ZERO,
            ),
        ),
    )

    assert pass_report.report_status == "pass"
    assert watch_report.report_status == "watch"
    assert block_report.report_status == "block"

    with pytest.raises(ValueError, match="status"):
        ResearchTeamCrossDomainReviewLoadRow(
            team_id="macro_review",
            domain_id="rates",
            active_review_count=d("1.000000"),
            active_review_points=d("1.000000"),
            capacity_points=d("10.000000"),
            capacity_load_ratio=d("0.100000"),
            overlap_domain_count=d("1.000000"),
            domain_overlap_pressure=d("0.333333"),
            catalyst_pressure_score=ZERO,
            evidence_age_seconds=ZERO,
            evidence_age_pressure=ZERO,
            sla_remaining_seconds=d("7200.000000"),
            sla_pressure=ZERO,
            review_load_score=d("0.035000"),
            status="review",
            reason_codes=("cross_domain_review_load_pass",),
        )


def test_cross_domain_review_load_requires_frozen_dataclasses_and_decimal_inputs() -> None:
    report = build((observation("macro_review", "rates"),))

    with pytest.raises(FrozenInstanceError):
        report.report_status = "watch"  # type: ignore[misc]

    for value in (report, report.rows[0]):
        assert is_dataclass(value)
        assert value.__dataclass_params__.frozen is True  # type: ignore[attr-defined]
        assert_decimal_numeric_fields(value)

    with pytest.raises(ValueError, match="Decimal"):
        observation("macro_review", "rates", active_review_points=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation("macro_review", "rates", catalyst_pressure_score=0.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(
            "macro_review",
            "rates",
            capacity_points=_DecimalSubclass("10.000000"),
        )


def test_cross_domain_review_load_rejects_raw_identifiers_and_unsafe_payloads() -> None:
    unsafe_names = (
        "raw_candidate_42",
        "event_id_42",
        "market_slug_alpha",
        "source_ref_99",
        "https://example.test/ref",
    )
    for value in unsafe_names:
        with pytest.raises(ValueError):
            observation(value, "rates")
        with pytest.raises(ValueError):
            observation("macro_review", value)

    report = build((observation("macro_review", "rates"),))
    public = repr(asdict(report)).lower()
    for value in unsafe_names:
        assert value.lower() not in public
    for field_name in fields(ResearchTeamCrossDomainReviewLoadObservation):
        assert field_name.name not in {
            "event_id",
            "market_id",
            "market_slug",
            "source_id",
            "source_reference",
            "source_url",
        }

    tampered = research_team_cross_domain_review_load_payload(report)
    tampered["rows"][0]["team_id"] = "raw_candidate_42"  # type: ignore[index]
    with pytest.raises(ValueError):
        research_team_cross_domain_review_load_payload(tampered)


def test_cross_domain_review_load_module_has_no_write_or_execution_surfaces() -> None:
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
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            elif isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names
