from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_market_category_coverage_report import (
    ResearchMarketCategoryCoverageConfig,
    ResearchMarketCategoryCoverageInputRow,
    ResearchMarketCategoryCoverageReasonCodeCount,
    ResearchMarketCategoryCoverageReport,
    ResearchMarketCategoryCoverageScoreRow,
    build_research_market_category_coverage_report,
    research_market_category_coverage_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedCoverageShape:
    category: str
    candidate_id: str
    source_families: tuple[str, ...]
    team_names: tuple[str, ...]
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchMarketCategoryCoverageConfig:
    values = {
        "config_version": "research-market-category-coverage-v0",
        "target_categories": (
            "basketball",
            "btc",
            "equity_index",
            "gold",
            "politics",
            "soccer",
        ),
        "min_candidate_count": d("3"),
        "min_source_family_count": d("3"),
        "min_team_count": d("2"),
        "pass_coverage_score": d("0.750000"),
        "watch_coverage_score": d("0.400000"),
        "candidate_weight": d("0.400000"),
        "source_weight": d("0.350000"),
        "team_weight": d("0.250000"),
    }
    values.update(overrides)
    return ResearchMarketCategoryCoverageConfig(**values)


def coverage(
    index: int,
    *,
    category: str = "politics",
    candidate_id: str | None = None,
    source_families: tuple[str, ...] = ("official",),
    team_names: tuple[str, ...] = ("macro",),
    reason_codes: tuple[str, ...] = (),
) -> ResearchMarketCategoryCoverageInputRow:
    return ResearchMarketCategoryCoverageInputRow(
        category=category,
        candidate_id=candidate_id or f"{category}-candidate-{index:03d}",
        source_families=source_families,
        team_names=team_names,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchMarketCategoryCoverageConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchMarketCategoryCoverageReport:
    return build_research_market_category_coverage_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_blocks_all_required_categories_with_zero_counts() -> None:
    coverage_report = report(())

    assert type(coverage_report) is ResearchMarketCategoryCoverageReport
    assert coverage_report.generated_at == GENERATED_AT
    assert coverage_report.config_version == "research-market-category-coverage-v0"
    assert coverage_report.category_count == d("6")
    assert coverage_report.input_row_count == d("0")
    assert coverage_report.pass_count == d("0")
    assert coverage_report.watch_count == d("0")
    assert coverage_report.blocked_count == d("6")
    assert coverage_report.average_coverage_score == d("0.000000")
    assert coverage_report.status == "blocked"
    assert coverage_report.reason_codes == ("no_category_coverage",)
    assert coverage_report.reason_code_counts == (
        ResearchMarketCategoryCoverageReasonCodeCount(
            reason_code="no_candidates",
            count=d("6"),
        ),
        ResearchMarketCategoryCoverageReasonCodeCount(
            reason_code="no_category_coverage",
            count=d("6"),
        ),
        ResearchMarketCategoryCoverageReasonCodeCount(
            reason_code="no_source_family_coverage",
            count=d("6"),
        ),
        ResearchMarketCategoryCoverageReasonCodeCount(
            reason_code="no_team_coverage",
            count=d("6"),
        ),
        ResearchMarketCategoryCoverageReasonCodeCount(
            reason_code="research_market_category_coverage_blocked",
            count=d("6"),
        ),
    )
    assert tuple(row.category for row in coverage_report.rows) == (
        "basketball",
        "btc",
        "equity_index",
        "gold",
        "politics",
        "soccer",
    )
    assert coverage_report.paper_only is True
    assert coverage_report.report_only is True
    assert coverage_report.readonly is True


def test_category_rows_score_candidate_source_and_team_coverage() -> None:
    coverage_report = report(
        (
            coverage(
                2,
                category="politics",
                source_families=("polling", "venue"),
                team_names=("macro", "research"),
            ),
            coverage(
                1,
                category="btc",
                source_families=("exchange",),
                team_names=("crypto",),
                reason_codes=("manual_queue_reviewed",),
            ),
            coverage(
                3,
                category="politics",
                source_families=("official",),
                team_names=("macro",),
            ),
            coverage(
                2,
                category="btc",
                source_families=("official",),
                team_names=("crypto",),
            ),
            coverage(
                1,
                category="politics",
                source_families=("official", "polling"),
                team_names=("macro",),
            ),
            coverage(
                1,
                category="gold",
                source_families=(),
                team_names=(),
            ),
        ),
    )

    assert coverage_report.status == "blocked"
    assert coverage_report.input_row_count == d("6")
    assert coverage_report.pass_count == d("1")
    assert coverage_report.watch_count == d("1")
    assert coverage_report.blocked_count == d("4")
    assert coverage_report.average_coverage_score == d("0.293056")

    btc_row = coverage_report.rows[1]
    assert type(btc_row) is ResearchMarketCategoryCoverageScoreRow
    assert btc_row.category == "btc"
    assert btc_row.candidate_count == d("2")
    assert btc_row.source_family_count == d("2")
    assert btc_row.team_count == d("1")
    assert btc_row.candidate_coverage_score == d("0.666667")
    assert btc_row.source_coverage_score == d("0.666667")
    assert btc_row.team_coverage_score == d("0.500000")
    assert btc_row.coverage_score == d("0.625000")
    assert btc_row.status == "watch"
    assert btc_row.candidate_ids == ("btc-candidate-001", "btc-candidate-002")
    assert btc_row.source_families == ("exchange", "official")
    assert btc_row.team_names == ("crypto",)
    assert btc_row.reason_codes == (
        "input_manual_queue_reviewed",
        "not_enough_candidates",
        "not_enough_source_families",
        "not_enough_team_coverage",
        "research_market_category_coverage_watch",
    )

    politics_row = coverage_report.rows[4]
    assert politics_row.category == "politics"
    assert politics_row.candidate_count == d("3")
    assert politics_row.source_family_count == d("3")
    assert politics_row.team_count == d("2")
    assert politics_row.coverage_score == d("1.000000")
    assert politics_row.status == "pass"
    assert politics_row.reason_codes == (
        "candidate_coverage_met",
        "research_market_category_coverage_pass",
        "source_family_coverage_met",
        "team_coverage_met",
    )


def test_payload_is_deterministic_public_and_float_free() -> None:
    coverage_report = report(
        (
            coverage(
                3,
                category="politics",
                source_families=("venue",),
                team_names=("research",),
            ),
            SuppliedCoverageShape(
                category="politics",
                candidate_id="politics-candidate-001",
                source_families=("official",),
                team_names=("macro",),
                reason_codes=("zeta", "alpha"),
            ),
            coverage(
                2,
                category="politics",
                source_families=("polling",),
                team_names=("macro",),
            ),
        ),
    )

    payload = research_market_category_coverage_report_payload(coverage_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert tuple(row.category for row in coverage_report.rows) == (
        "basketball",
        "btc",
        "equity_index",
        "gold",
        "politics",
        "soccer",
    )
    assert coverage_report.rows[4].candidate_ids == (
        "politics-candidate-001",
        "politics-candidate-002",
        "politics-candidate-003",
    )
    assert coverage_report.rows[4].reason_codes == (
        "candidate_coverage_met",
        "input_alpha",
        "input_zeta",
        "research_market_category_coverage_pass",
        "source_family_coverage_met",
        "team_coverage_met",
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][4]["coverage_score"] == "1.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    assert all(
        unsafe not in encoded.lower()
        for unsafe in ("private_key", "wallet", "balance", "create_order")
    )


def test_validation_rejects_bad_types_unknown_categories_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="candidate_weight"):
        config(candidate_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_coverage_score"):
        config(pass_coverage_score=0.75)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_candidate_count"):
        config(min_candidate_count=_DecimalSubclass("3"))
    with pytest.raises(ValueError, match="generated_at"):
        report((coverage(1),), generated_at=datetime(2026, 7, 6, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report((coverage(1),), generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="category"):
        coverage(1, category=" politics")
    with pytest.raises(ValueError, match="source_families"):
        coverage(1, source_families=("Official",))
    with pytest.raises(ValueError, match="reason_codes"):
        coverage(1, reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="target_categories"):
        report((coverage(1, category="hockey"),))
    with pytest.raises(ValueError, match="paper_only"):
        replace(coverage(1), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    coverage_report = report(
        (
            coverage(1, source_families=("official",), team_names=("macro",)),
            coverage(2, source_families=("polling",), team_names=("research",)),
            coverage(3, source_families=("venue",), team_names=("macro",)),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        coverage_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        coverage_report.rows[4].coverage_score = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="coverage_score"):
        replace(coverage_report.rows[4], coverage_score=d("0.100000"))
    with pytest.raises(ValueError, match="status"):
        replace(coverage_report, status="pass")


def test_owned_module_has_no_network_database_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_market_category_coverage_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "pathlib",
        "open(",
        "connect(",
        "sqlalchemy",
        "psycopg",
        "web3",
        "create_order",
        "cancel_order",
        "market_order",
        "limit_order",
        "private_key",
        "wallet",
        "balance",
    )

    assert all(term not in source for term in forbidden_terms)


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
