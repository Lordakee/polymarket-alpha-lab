from __future__ import annotations

from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_ambiguity_root_cause_report import (
    ROOT_CAUSES,
    STATUSES,
    ResearchResolutionAmbiguityRootCauseAggregate,
    ResearchResolutionAmbiguityRootCauseConfig,
    ResearchResolutionAmbiguityRootCauseReport,
    ResearchResolutionAmbiguityRootCauseRow,
    build_research_resolution_ambiguity_root_cause_report,
    research_resolution_ambiguity_root_cause_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 14, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionAmbiguityRootCauseConfig:
    values = {
        "config_version": "research-resolution-ambiguity-root-cause-v0",
        "watch_pressure_threshold": d("0.250000"),
        "block_pressure_threshold": d("0.550000"),
        "oracle_lag_block_minutes": d("120.000000"),
        "edge_case_block_count": d("5"),
        "rule_clarity_weight": d("0.250000"),
        "source_consistency_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.250000"),
        "oracle_lag_weight": d("0.150000"),
        "edge_case_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchResolutionAmbiguityRootCauseConfig(**values)


def aggregate(**overrides: object) -> ResearchResolutionAmbiguityRootCauseAggregate:
    values = {
        "rule_clarity_score": d("0.900000"),
        "source_consistency_score": d("0.800000"),
        "contradiction_pressure_score": d("0.100000"),
        "oracle_lag_minutes": d("24.000000"),
        "edge_case_count": d("1"),
    }
    values.update(overrides)
    return ResearchResolutionAmbiguityRootCauseAggregate(**values)


def report(
    metrics: ResearchResolutionAmbiguityRootCauseAggregate | object | None = None,
    *,
    cfg: ResearchResolutionAmbiguityRootCauseConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionAmbiguityRootCauseReport:
    return build_research_resolution_ambiguity_root_cause_report(
        metrics or aggregate(),
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_low_aggregate_pressure_passes_with_public_safe_root_causes() -> None:
    root_report = report()

    assert STATUSES == ("pass", "watch", "block")
    assert ROOT_CAUSES == (
        "rule_clarity_gap",
        "source_consistency_gap",
        "contradiction_pressure",
        "oracle_lag",
        "edge_case_pressure",
    )
    assert type(root_report) is ResearchResolutionAmbiguityRootCauseReport
    assert root_report.status == "pass"
    assert root_report.ambiguity_pressure_score == d("0.150000")
    assert root_report.block_count == d("0")
    assert root_report.watch_count == d("0")
    assert root_report.pass_count == d("5")
    assert root_report.reason_codes == ("resolution_ambiguity_root_cause_pass",)
    assert root_report.paper_only is True
    assert root_report.report_only is True
    assert root_report.readonly is True

    rows = root_report.rows
    assert tuple(row.root_cause for row in rows) == ROOT_CAUSES
    assert tuple(type(row) for row in rows) == (ResearchResolutionAmbiguityRootCauseRow,) * 5
    assert rows[0].aggregate_value == d("0.900000")
    assert rows[0].pressure_score == d("0.100000")
    assert rows[0].weighted_pressure_score == d("0.025000")
    assert rows[0].status == "pass"
    assert rows[0].reason_codes == ("rule_clarity_gap_low",)
    assert rows[3].aggregate_value == d("24.000000")
    assert rows[3].pressure_score == d("0.200000")
    assert rows[4].aggregate_value == d("1")
    assert rows[4].pressure_score == d("0.200000")


def test_high_root_cause_pressure_blocks_and_counts_causes() -> None:
    root_report = report(
        aggregate(
            rule_clarity_score=d("0.200000"),
            source_consistency_score=d("0.300000"),
            contradiction_pressure_score=d("0.800000"),
            oracle_lag_minutes=d("180.000000"),
            edge_case_count=d("6"),
        ),
    )

    assert root_report.status == "block"
    assert root_report.ambiguity_pressure_score == d("0.840000")
    assert root_report.block_count == d("5")
    assert root_report.watch_count == d("0")
    assert root_report.pass_count == d("0")
    assert root_report.reason_codes == ("resolution_ambiguity_root_cause_block",)
    assert tuple(row.status for row in root_report.rows) == ("block",) * 5
    assert tuple(row.pressure_score for row in root_report.rows) == (
        d("0.800000"),
        d("0.700000"),
        d("0.800000"),
        d("1.000000"),
        d("1.000000"),
    )


def test_payload_and_digest_are_deterministic_decimal_only_and_sanitized() -> None:
    left = report(
        aggregate(
            rule_clarity_score=d("0.600000"),
            source_consistency_score=d("0.500000"),
            contradiction_pressure_score=d("0.400000"),
            oracle_lag_minutes=d("60.000000"),
            edge_case_count=d("2"),
        ),
    )
    right = report(
        aggregate(
            rule_clarity_score=d("0.600000"),
            source_consistency_score=d("0.500000"),
            contradiction_pressure_score=d("0.400000"),
            oracle_lag_minutes=d("60.000000"),
            edge_case_count=d("2"),
        ),
    )

    payload = research_resolution_ambiguity_root_cause_report_payload(left)
    encoded = json.dumps(payload, sort_keys=True)

    assert left.derived_validation_digest == right.derived_validation_digest
    assert len(left.derived_validation_digest) == 64
    assert all(character in "0123456789abcdef" for character in left.derived_validation_digest)
    assert payload["derived_validation_digest"] == left.derived_validation_digest
    assert payload["generated_at"] == "2026-07-08T14:00:00+00:00"
    assert payload["ambiguity_pressure_score"] == "0.435000"
    assert payload["rows"][0]["derived_validation_digest"] == left.rows[0].derived_validation_digest
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded
    for sensitive_key in (
        "source_url",
        "source_text",
        "source_ref",
        "raw_source",
        "market_id",
        "market_slug",
        "condition_id",
        "question",
        "recommendation",
        "sizing",
    ):
        assert sensitive_key not in encoded.lower()


def test_validation_rejects_bad_numeric_types_statuses_flags_and_tampering() -> None:
    with pytest.raises(ValueError, match="rule_clarity_score"):
        aggregate(rule_clarity_score=0.9)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_consistency_score"):
        aggregate(source_consistency_score=_DecimalSubclass("0.800000"))
    with pytest.raises(ValueError, match="edge_case_count"):
        aggregate(edge_case_count=d("1.500000"))
    with pytest.raises(ValueError, match="watch_pressure_threshold"):
        config(watch_pressure_threshold=d("0.600000"))
    with pytest.raises(ValueError, match="rule_clarity_weight"):
        config(rule_clarity_weight=d("0.240000"))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=datetime(2026, 7, 8, 14, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(generated_at=_DatetimeSubclass(2026, 7, 8, 14, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="paper_only"):
        replace(aggregate(), paper_only=False)

    root_report = report()
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(root_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="status"):
        replace(root_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="weighted_pressure_score"):
        replace(root_report.rows[0], weighted_pressure_score=d("0.200000"))


def test_public_dataclasses_are_frozen() -> None:
    root_report = report()

    with pytest.raises(FrozenInstanceError):
        root_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        root_report.rows[0].pressure_score = d("0")  # type: ignore[misc]


def test_owned_module_has_no_network_db_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_ambiguity_root_cause_report.py"
    )
    source = module_path.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "sqlite",
        "psycopg",
        "sqlalchemy",
        "connect(",
        "open(",
        "wallet",
        "auth",
        "private_key",
        "create_order",
        "cancel_order",
        "post(",
        "trade",
        "recommendation",
        "sizing",
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
