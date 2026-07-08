from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_resolution_source_lag_sla_report import (
    ResearchResolutionSourceLagSlaConfig,
    ResearchResolutionSourceLagSlaInput,
    ResearchResolutionSourceLagSlaReasonCodeCount,
    ResearchResolutionSourceLagSlaReport,
    ResearchResolutionSourceLagSlaRow,
    STATUSES,
    build_research_resolution_source_lag_sla_report,
    research_resolution_source_lag_sla_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedSlaShape:
    public_resolution_key: str
    authoritative_source_lag_seconds: Decimal
    secondary_corroboration_lag_seconds: Decimal
    ambiguity_pressure: Decimal
    unresolved_outcome_queue_age_seconds: Decimal
    manual_escalation_urgency: Decimal
    reason_codes: tuple[str, ...] = ()
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchResolutionSourceLagSlaConfig:
    values = {
        "authoritative_source_watch_lag_seconds": d("1800"),
        "authoritative_source_block_lag_seconds": d("14400"),
        "secondary_corroboration_watch_lag_seconds": d("3600"),
        "secondary_corroboration_block_lag_seconds": d("21600"),
        "unresolved_queue_watch_age_seconds": d("43200"),
        "unresolved_queue_block_age_seconds": d("172800"),
        "watch_pressure_threshold": d("0.350000"),
        "block_pressure_threshold": d("0.700000"),
        "authoritative_source_lag_weight": d("0.300000"),
        "secondary_corroboration_lag_weight": d("0.200000"),
        "ambiguity_pressure_weight": d("0.200000"),
        "unresolved_queue_age_weight": d("0.200000"),
        "manual_escalation_urgency_weight": d("0.100000"),
    }
    values.update(overrides)
    return ResearchResolutionSourceLagSlaConfig(**values)


def sla_item(
    public_resolution_key: str = "case-a",
    *,
    authoritative_source_lag_seconds: Decimal = d("600"),
    secondary_corroboration_lag_seconds: Decimal = d("900"),
    ambiguity_pressure: Decimal = d("0.050000"),
    unresolved_outcome_queue_age_seconds: Decimal = d("3600"),
    manual_escalation_urgency: Decimal = d("0.100000"),
    reason_codes: tuple[str, ...] = (),
) -> ResearchResolutionSourceLagSlaInput:
    return ResearchResolutionSourceLagSlaInput(
        public_resolution_key=public_resolution_key,
        authoritative_source_lag_seconds=authoritative_source_lag_seconds,
        secondary_corroboration_lag_seconds=secondary_corroboration_lag_seconds,
        ambiguity_pressure=ambiguity_pressure,
        unresolved_outcome_queue_age_seconds=unresolved_outcome_queue_age_seconds,
        manual_escalation_urgency=manual_escalation_urgency,
        reason_codes=reason_codes,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchResolutionSourceLagSlaConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchResolutionSourceLagSlaReport:
    return build_research_resolution_source_lag_sla_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_report_only_pass_with_zero_digest_surface() -> None:
    sla_report = report(())

    assert STATUSES == ("pass", "watch", "block")
    assert type(sla_report) is ResearchResolutionSourceLagSlaReport
    assert sla_report.generated_at == GENERATED_AT
    assert sla_report.resolution_count == d("0")
    assert sla_report.pass_count == d("0")
    assert sla_report.watch_count == d("0")
    assert sla_report.block_count == d("0")
    assert sla_report.average_sla_pressure is None
    assert sla_report.max_authoritative_source_lag_seconds == d("0")
    assert sla_report.max_secondary_corroboration_lag_seconds == d("0")
    assert sla_report.max_unresolved_outcome_queue_age_seconds == d("0")
    assert sla_report.status == "pass"
    assert sla_report.reason_codes == ("no_resolution_source_lag_sla_items",)
    assert sla_report.reason_code_counts == (
        ResearchResolutionSourceLagSlaReasonCodeCount(
            reason_code="no_resolution_source_lag_sla_items",
            count=d("1"),
        ),
    )
    assert sla_report.rows == ()
    assert len(sla_report.derived_validation_digest) == 64
    assert sla_report.paper_only is True
    assert sla_report.report_only is True
    assert sla_report.readonly is True


def test_sla_report_aggregates_lags_ambiguity_queue_age_and_escalation() -> None:
    sla_report = report(
        (
            sla_item(
                "case-c",
                authoritative_source_lag_seconds=d("28800"),
                secondary_corroboration_lag_seconds=d("43200"),
                ambiguity_pressure=d("0.800000"),
                unresolved_outcome_queue_age_seconds=d("259200"),
                manual_escalation_urgency=d("0.900000"),
                reason_codes=("manual_public_review",),
            ),
            sla_item("case-a"),
            sla_item(
                "case-b",
                authoritative_source_lag_seconds=d("7200"),
                secondary_corroboration_lag_seconds=d("10800"),
                ambiguity_pressure=d("0.350000"),
                unresolved_outcome_queue_age_seconds=d("86400"),
                manual_escalation_urgency=d("0.400000"),
            ),
        ),
    )

    assert tuple(row.public_resolution_key for row in sla_report.rows) == (
        "case-a",
        "case-b",
        "case-c",
    )
    assert sla_report.status == "block"
    assert sla_report.resolution_count == d("3")
    assert sla_report.pass_count == d("1")
    assert sla_report.watch_count == d("1")
    assert sla_report.block_count == d("1")
    assert sla_report.average_sla_pressure == d("0.485000")
    assert sla_report.max_authoritative_source_lag_seconds == d("28800")
    assert sla_report.max_secondary_corroboration_lag_seconds == d("43200")
    assert sla_report.max_unresolved_outcome_queue_age_seconds == d("259200")

    pass_row, watch_row, block_row = sla_report.rows
    assert type(pass_row) is ResearchResolutionSourceLagSlaRow
    assert pass_row.authoritative_source_lag_pressure == d("0.041667")
    assert pass_row.secondary_corroboration_lag_pressure == d("0.041667")
    assert pass_row.unresolved_outcome_queue_age_pressure == d("0.020833")
    assert pass_row.sla_pressure == d("0.045000")
    assert pass_row.status == "pass"

    assert watch_row.authoritative_source_lag_pressure == d("0.500000")
    assert watch_row.secondary_corroboration_lag_pressure == d("0.500000")
    assert watch_row.unresolved_outcome_queue_age_pressure == d("0.500000")
    assert watch_row.sla_pressure == d("0.460000")
    assert watch_row.status == "watch"

    assert block_row.authoritative_source_lag_pressure == d("1.000000")
    assert block_row.secondary_corroboration_lag_pressure == d("1.000000")
    assert block_row.unresolved_outcome_queue_age_pressure == d("1.000000")
    assert block_row.sla_pressure == d("0.950000")
    assert block_row.status == "block"
    assert "input_manual_public_review" in block_row.reason_codes
    assert sla_report.reason_code_counts == tuple(
        sorted(sla_report.reason_code_counts, key=lambda item: item.reason_code),
    )


def test_payload_and_digest_are_deterministic_public_safe_and_decimal_strings() -> None:
    rows = (
        SuppliedSlaShape(
            public_resolution_key="case-b",
            authoritative_source_lag_seconds=d("7200"),
            secondary_corroboration_lag_seconds=d("10800"),
            ambiguity_pressure=d("0.350000"),
            unresolved_outcome_queue_age_seconds=d("86400"),
            manual_escalation_urgency=d("0.400000"),
            reason_codes=("manual_public_review",),
        ),
        sla_item("case-a"),
    )

    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))
    first_payload = research_resolution_source_lag_sla_report_payload(first_report)
    second_payload = research_resolution_source_lag_sla_report_payload(second_report)
    encoded = json.dumps(first_payload, sort_keys=True)

    assert first_payload == second_payload
    assert first_report.derived_validation_digest == second_report.derived_validation_digest
    assert first_payload["derived_validation_digest"] == first_report.derived_validation_digest
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["rows"][0]["sla_pressure"] == "0.045000"
    assert first_payload["rows"][1]["secondary_corroboration_lag_seconds"] == "10800.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(first_payload))
    assert all(not isinstance(value, Decimal) for value in _walk_payload_values(first_payload))
    assert all(
        fragment not in encoded.lower()
        for fragment in (
            "http",
            "source_url",
            "source_text",
            "source_ref",
            "raw_source",
            "market_slug",
            "market_id",
            "condition_id",
            "wallet",
            "auth_token",
            "oauth",
            "api_key",
            "order",
            "trade",
            "recommendation",
            "sizing",
        )
    )


def test_validation_rejects_bad_types_thresholds_flags_and_unsafe_public_values() -> None:
    with pytest.raises(ValueError, match="authoritative_source_lag_weight"):
        config(authoritative_source_lag_weight=d("0.100000"))
    with pytest.raises(ValueError, match="block_pressure_threshold"):
        config(block_pressure_threshold=d("0.300000"))
    with pytest.raises(ValueError, match="authoritative_source_block_lag_seconds"):
        config(authoritative_source_block_lag_seconds=d("1000"))
    with pytest.raises(ValueError, match="secondary_corroboration_watch_lag_seconds"):
        config(secondary_corroboration_watch_lag_seconds=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="manual_escalation_urgency_weight"):
        config(manual_escalation_urgency_weight=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="generated_at"):
        report((sla_item(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (sla_item(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="public_resolution_key"):
        sla_item(public_resolution_key="case url")
    with pytest.raises(ValueError, match="public_resolution_key"):
        sla_item(public_resolution_key="market-alpha")
    with pytest.raises(ValueError, match="authoritative_source_lag_seconds"):
        sla_item(authoritative_source_lag_seconds=600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="secondary_corroboration_lag_seconds"):
        sla_item(secondary_corroboration_lag_seconds=d("-1"))
    with pytest.raises(ValueError, match="ambiguity_pressure"):
        sla_item(ambiguity_pressure=d("1.100000"))
    with pytest.raises(ValueError, match="manual_escalation_urgency"):
        sla_item(manual_escalation_urgency=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="reason_codes"):
        sla_item(reason_codes=("Needs Review",))
    with pytest.raises(ValueError, match="paper_only"):
        replace(sla_item(), paper_only=False)


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    sla_report = report((sla_item(),))

    with pytest.raises(FrozenInstanceError):
        sla_report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        sla_report.rows[0].sla_pressure = d("0")  # type: ignore[misc]
    with pytest.raises(TypeError):
        type("BadConfig", (ResearchResolutionSourceLagSlaConfig,), {})
    with pytest.raises(ValueError, match="status"):
        replace(sla_report.rows[0], status="blocked")
    with pytest.raises(ValueError, match="sla_pressure"):
        replace(sla_report.rows[0], sla_pressure=d("0.999999"))
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(sla_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="resolution_count"):
        replace(sla_report, resolution_count=d("2"))


def test_owned_module_has_no_db_network_execution_or_advice_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_resolution_source_lag_sla_report.py"
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
        "psycopg",
        "sqlalchemy",
        "sqlite",
        "supabase",
        ".write(",
        "db_",
        "wallet",
        "auth_token",
        "oauth",
        "api_key",
        "order",
        "trade",
        "live execution",
        "execute(",
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
