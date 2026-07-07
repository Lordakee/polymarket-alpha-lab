from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_outcome_taxonomy_report import (
    ResearchEventOutcomeTaxonomyConfig,
    ResearchEventOutcomeTaxonomyFinding,
    ResearchEventOutcomeTaxonomyOutcome,
    ResearchEventOutcomeTaxonomyReport,
    build_research_event_outcome_taxonomy_report,
    research_event_outcome_taxonomy_report_payload,
)


GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventOutcomeTaxonomyConfig:
    values = {
        "config_version": "research-event-outcome-taxonomy-report-v0",
        "ambiguity_watch_threshold": d("0.250000"),
        "ambiguity_block_threshold": d("0.600000"),
        "min_outcome_count": d("2"),
    }
    values.update(overrides)
    return ResearchEventOutcomeTaxonomyConfig(**values)


def outcome(
    outcome_id: str,
    *,
    coverage_keys: tuple[str, ...],
    settlement_keys: tuple[str, ...],
    covers_residual: bool = False,
    ambiguity_risk: Decimal = d("0.000000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchEventOutcomeTaxonomyOutcome:
    return ResearchEventOutcomeTaxonomyOutcome(
        outcome_id=outcome_id,
        coverage_keys=coverage_keys,
        settlement_keys=settlement_keys,
        covers_residual=covers_residual,
        ambiguity_risk=ambiguity_risk,
        reason_codes=reason_codes,
    )


def report(
    outcomes: tuple[ResearchEventOutcomeTaxonomyOutcome, ...],
    *,
    expected_coverage_keys: tuple[str, ...] = ("dem", "gop", "other"),
    cfg: ResearchEventOutcomeTaxonomyConfig | None = None,
    event_ref: str = "Will the raw question slug resolve from https://source.example/dsn/table? token=secret",
) -> ResearchEventOutcomeTaxonomyReport:
    return build_research_event_outcome_taxonomy_report(
        event_ref=event_ref,
        outcomes=outcomes,
        expected_coverage_keys=expected_coverage_keys,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_complete_disjoint_taxonomy_passes_with_deterministic_payload() -> None:
    taxonomy_report = report(
        (
            outcome(
                "republican",
                coverage_keys=("gop",),
                settlement_keys=("gop_win",),
            ),
            outcome(
                "democrat",
                coverage_keys=("dem",),
                settlement_keys=("dem_win",),
            ),
            outcome(
                "other",
                coverage_keys=("other",),
                settlement_keys=("other_win",),
                covers_residual=True,
                reason_codes=("manual_resolution_reviewed",),
            ),
        ),
    )

    payload = research_event_outcome_taxonomy_report_payload(taxonomy_report)
    encoded = json.dumps(payload, sort_keys=True)

    assert type(taxonomy_report) is ResearchEventOutcomeTaxonomyReport
    assert taxonomy_report.generated_at == GENERATED_AT
    assert taxonomy_report.status == "pass"
    assert taxonomy_report.outcome_count == d("3")
    assert taxonomy_report.coverage_key_count == d("3")
    assert taxonomy_report.settlement_key_count == d("3")
    assert taxonomy_report.watch_count == d("0")
    assert taxonomy_report.blocked_count == d("0")
    assert taxonomy_report.reason_codes == ("outcome_taxonomy_pass",)
    assert tuple(row.outcome_id for row in taxonomy_report.rows) == (
        "democrat",
        "other",
        "republican",
    )
    assert taxonomy_report.rows[1].reason_codes == (
        "input_manual_resolution_reviewed",
        "outcome_taxonomy_pass",
        "residual_outcome_declared",
    )
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["ambiguity_risk"] == "0.000000"
    assert payload["redacted_event_ref"].startswith("event_")
    assert "raw question" not in encoded
    assert "source.example" not in encoded
    assert "token=secret" not in encoded
    assert "slug" not in encoded
    assert "dsn" not in encoded
    assert "table" not in encoded
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert not any(_unsafe_public_key(key) for key in _walk_payload_keys(payload))


def test_overlap_missing_coverage_and_shared_settlement_key_block_report() -> None:
    taxonomy_report = report(
        (
            outcome(
                "democrat",
                coverage_keys=("dem", "recount"),
                settlement_keys=("winner_declared",),
            ),
            outcome(
                "republican",
                coverage_keys=("gop", "recount"),
                settlement_keys=("winner_declared",),
            ),
        ),
    )

    assert taxonomy_report.status == "blocked"
    assert taxonomy_report.blocked_count == d("3")
    assert taxonomy_report.watch_count == d("1")
    assert taxonomy_report.reason_codes == (
        "coverage_key_overlap",
        "missing_expected_coverage",
        "missing_residual_outcome",
        "settlement_key_overlap",
    )
    assert taxonomy_report.findings == (
        ResearchEventOutcomeTaxonomyFinding(
            check_name="mutual_exclusivity",
            severity="blocked",
            reason_code="coverage_key_overlap",
            outcome_ids=("democrat", "republican"),
            detail_key="recount",
        ),
        ResearchEventOutcomeTaxonomyFinding(
            check_name="exhaustiveness",
            severity="blocked",
            reason_code="missing_expected_coverage",
            outcome_ids=(),
            detail_key="other",
        ),
        ResearchEventOutcomeTaxonomyFinding(
            check_name="exhaustiveness",
            severity="watch",
            reason_code="missing_residual_outcome",
            outcome_ids=(),
            detail_key="residual",
        ),
        ResearchEventOutcomeTaxonomyFinding(
            check_name="settlement_mapping",
            severity="blocked",
            reason_code="settlement_key_overlap",
            outcome_ids=("democrat", "republican"),
            detail_key="winner_declared",
        ),
    )


def test_missing_settlement_mapping_and_ambiguity_thresholds_drive_watch_or_block() -> None:
    watch_report = report(
        (
            outcome(
                "democrat",
                coverage_keys=("dem",),
                settlement_keys=("dem_win",),
                ambiguity_risk=d("0.250000"),
            ),
            outcome(
                "republican",
                coverage_keys=("gop",),
                settlement_keys=("gop_win",),
            ),
            outcome(
                "other",
                coverage_keys=("other",),
                settlement_keys=("other_win",),
                covers_residual=True,
            ),
        ),
    )
    block_report = report(
        (
            outcome(
                "democrat",
                coverage_keys=("dem",),
                settlement_keys=(),
            ),
            outcome(
                "republican",
                coverage_keys=("gop",),
                settlement_keys=("gop_win",),
                ambiguity_risk=d("0.600000"),
            ),
            outcome(
                "other",
                coverage_keys=("other",),
                settlement_keys=("other_win",),
                covers_residual=True,
            ),
        ),
    )

    assert watch_report.status == "watch"
    assert watch_report.reason_codes == ("ambiguity_risk_watch",)
    assert block_report.status == "blocked"
    assert block_report.reason_codes == (
        "ambiguity_risk_blocked",
        "missing_settlement_mapping",
    )


def test_validation_rejects_bad_types_unknown_statuses_and_bad_flags() -> None:
    with pytest.raises(ValueError, match="ambiguity_watch_threshold"):
        config(ambiguity_watch_threshold=d("0.600000"))
    with pytest.raises(ValueError, match="ambiguity_block_threshold"):
        config(ambiguity_block_threshold=d("0.250000"))
    with pytest.raises(ValueError, match="min_outcome_count"):
        config(min_outcome_count=_DecimalSubclass("2"))
    with pytest.raises(ValueError, match="ambiguity_risk"):
        outcome(
            "democrat",
            coverage_keys=("dem",),
            settlement_keys=("dem_win",),
            ambiguity_risk=0.1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_outcome_taxonomy_report(
            event_ref="event",
            outcomes=(),
            expected_coverage_keys=(),
            config=config(),
            generated_at=datetime(2026, 7, 6, 12, 0),
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_research_event_outcome_taxonomy_report(
            event_ref="event",
            outcomes=(),
            expected_coverage_keys=(),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 6, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="outcome_id"):
        outcome("Democrat", coverage_keys=("dem",), settlement_keys=("dem_win",))
    with pytest.raises(ValueError, match="coverage_keys"):
        outcome("democrat", coverage_keys=["dem"], settlement_keys=("dem_win",))  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settlement_keys"):
        outcome("democrat", coverage_keys=("dem",), settlement_keys=("Win",))
    with pytest.raises(ValueError, match="covers_residual"):
        replace(
            outcome("democrat", coverage_keys=("dem",), settlement_keys=("dem_win",)),
            covers_residual=1,  # type: ignore[arg-type]
        )
    with pytest.raises(ValueError, match="reason_codes"):
        outcome(
            "democrat",
            coverage_keys=("dem",),
            settlement_keys=("dem_win",),
            reason_codes=("Manual Review",),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(
            outcome("democrat", coverage_keys=("dem",), settlement_keys=("dem_win",)),
            paper_only=False,
        )


def test_public_dataclasses_are_frozen_and_manual_report_consistency_is_checked() -> None:
    taxonomy_report = report(
        (
            outcome("democrat", coverage_keys=("dem",), settlement_keys=("dem_win",)),
            outcome("republican", coverage_keys=("gop",), settlement_keys=("gop_win",)),
            outcome(
                "other",
                coverage_keys=("other",),
                settlement_keys=("other_win",),
                covers_residual=True,
            ),
        ),
    )

    with pytest.raises(FrozenInstanceError):
        taxonomy_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        taxonomy_report.rows[0].ambiguity_risk = d("0.500000")  # type: ignore[misc]
    with pytest.raises(ValueError, match="status"):
        replace(taxonomy_report, status="blocked")
    with pytest.raises(ValueError, match="outcome_count"):
        replace(taxonomy_report, outcome_count=d("4"))


def test_owned_module_has_no_trading_db_network_or_filesystem_write_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_outcome_taxonomy_report.py"
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
        "execute(",
        "insert ",
        "update ",
        "delete ",
        "order",
        "trade",
        "wallet",
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


def _walk_payload_keys(value: object) -> tuple[str, ...]:
    keys: list[str] = []
    if isinstance(value, dict):
        for key, item in value.items():
            keys.append(key)
            keys.extend(_walk_payload_keys(item))
    elif isinstance(value, list):
        for item in value:
            keys.extend(_walk_payload_keys(item))
    return tuple(keys)


def _unsafe_public_key(key: str) -> bool:
    return any(
        fragment in key.lower()
        for fragment in (
            "raw",
            "question",
            "slug",
            "source_url",
            "url",
            "text",
            "dsn",
            "table",
            "token",
        )
    )
