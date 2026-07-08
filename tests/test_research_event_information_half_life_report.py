from __future__ import annotations

from dataclasses import FrozenInstanceError, dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.research_event_information_half_life_report import (
    ResearchEventInformationHalfLifeConfig,
    ResearchEventInformationHalfLifeDomainSignal,
    ResearchEventInformationHalfLifeReasonCodeCount,
    ResearchEventInformationHalfLifeReport,
    ResearchEventInformationHalfLifeRow,
    build_research_event_information_half_life_report,
    research_event_information_half_life_report_digest,
    research_event_information_half_life_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


@dataclass(frozen=True)
class SuppliedDomainSignalShape:
    event_domain: str
    aggregate_source_update_cadence_seconds: Decimal
    aggregate_catalyst_frequency_seconds: Decimal
    aggregate_contradiction_decay_seconds: Decimal
    resolution_proximity_seconds: Decimal
    domain_observation_count: Decimal
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchEventInformationHalfLifeConfig:
    values = {
        "config_version": "research-event-information-half-life-v0",
        "pass_half_life_seconds": d("14400"),
        "watch_half_life_seconds": d("3600"),
        "min_domain_observation_count": d("3"),
        "source_update_weight": d("0.350000"),
        "catalyst_frequency_weight": d("0.250000"),
        "contradiction_decay_weight": d("0.250000"),
        "resolution_proximity_weight": d("0.150000"),
    }
    values.update(overrides)
    return ResearchEventInformationHalfLifeConfig(**values)


def signal(
    *,
    event_domain: str = "sports",
    source_update: Decimal = d("3600"),
    catalyst_frequency: Decimal = d("7200"),
    contradiction_decay: Decimal = d("10800"),
    resolution_proximity: Decimal = d("86400"),
    observation_count: Decimal = d("10"),
) -> ResearchEventInformationHalfLifeDomainSignal:
    return ResearchEventInformationHalfLifeDomainSignal(
        event_domain=event_domain,
        aggregate_source_update_cadence_seconds=source_update,
        aggregate_catalyst_frequency_seconds=catalyst_frequency,
        aggregate_contradiction_decay_seconds=contradiction_decay,
        resolution_proximity_seconds=resolution_proximity,
        domain_observation_count=observation_count,
    )


def supplied_signal(**overrides: object) -> SuppliedDomainSignalShape:
    values = {
        "event_domain": "macro-data",
        "aggregate_source_update_cadence_seconds": d("7200"),
        "aggregate_catalyst_frequency_seconds": d("10800"),
        "aggregate_contradiction_decay_seconds": d("14400"),
        "resolution_proximity_seconds": d("28800"),
        "domain_observation_count": d("4"),
    }
    values.update(overrides)
    return SuppliedDomainSignalShape(**values)


def report(
    rows: tuple[object, ...],
    *,
    cfg: ResearchEventInformationHalfLifeConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchEventInformationHalfLifeReport:
    return build_research_event_information_half_life_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_empty_input_returns_block_report_only_report() -> None:
    half_life_report = report(())

    assert type(half_life_report) is ResearchEventInformationHalfLifeReport
    assert half_life_report.generated_at == GENERATED_AT
    assert half_life_report.config_version == "research-event-information-half-life-v0"
    assert half_life_report.domain_count == d("0")
    assert half_life_report.pass_count == d("0")
    assert half_life_report.watch_count == d("0")
    assert half_life_report.block_count == d("0")
    assert half_life_report.average_estimated_half_life_seconds is None
    assert half_life_report.status == "block"
    assert half_life_report.reason_codes == ("no_event_domain_signals",)
    assert half_life_report.reason_code_counts == (
        ResearchEventInformationHalfLifeReasonCodeCount(
            reason_code="no_event_domain_signals",
            count=d("1"),
        ),
    )
    assert half_life_report.rows == ()
    assert half_life_report.paper_only is True
    assert half_life_report.report_only is True
    assert half_life_report.readonly is True


def test_domain_half_life_rows_use_all_aggregate_components_and_statuses() -> None:
    half_life_report = report(
        (
            signal(
                event_domain="weather",
                source_update=d("900"),
                catalyst_frequency=d("1800"),
                contradiction_decay=d("2400"),
                resolution_proximity=d("3600"),
                observation_count=d("6"),
            ),
            signal(event_domain="sports"),
            supplied_signal(),
        ),
    )

    assert half_life_report.status == "block"
    assert half_life_report.domain_count == d("3")
    assert half_life_report.pass_count == d("1")
    assert half_life_report.watch_count == d("1")
    assert half_life_report.block_count == d("1")
    assert half_life_report.average_estimated_half_life_seconds == d("11255.000000")
    assert tuple(row.event_domain for row in half_life_report.rows) == (
        "macro-data",
        "sports",
        "weather",
    )

    macro, sports, weather = half_life_report.rows
    assert type(macro) is ResearchEventInformationHalfLifeRow
    assert macro.estimated_half_life_seconds == d("13140.000000")
    assert macro.status == "watch"
    assert macro.reason_codes == (
        "event_information_half_life_watch",
        "medium_public_information_half_life",
        "resolution_buffer_present",
        "sufficient_domain_observations",
    )

    assert sports.source_update_component_seconds == d("1260.000000")
    assert sports.catalyst_frequency_component_seconds == d("1800.000000")
    assert sports.contradiction_decay_component_seconds == d("2700.000000")
    assert sports.resolution_proximity_component_seconds == d("12960.000000")
    assert sports.estimated_half_life_seconds == d("18720.000000")
    assert sports.status == "pass"

    assert weather.estimated_half_life_seconds == d("1905.000000")
    assert weather.status == "block"
    assert weather.reason_codes == (
        "event_information_half_life_block",
        "near_resolution",
        "short_public_information_half_life",
        "sufficient_domain_observations",
    )


def test_payload_and_digest_are_deterministic_without_float_values_or_raw_ids() -> None:
    rows = (
        signal(event_domain="sports"),
        supplied_signal(),
        signal(
            event_domain="weather",
            source_update=d("900"),
            catalyst_frequency=d("1800"),
            contradiction_decay=d("2400"),
            resolution_proximity=d("3600"),
            observation_count=d("6"),
        ),
    )
    first_report = report(rows)
    second_report = report(tuple(reversed(rows)))

    payload = research_event_information_half_life_report_payload(first_report)
    encoded = json.dumps(payload, sort_keys=True)
    digest = research_event_information_half_life_report_digest(first_report)

    assert payload == research_event_information_half_life_report_payload(second_report)
    assert digest == research_event_information_half_life_report_digest(second_report)
    assert len(digest) == 64
    assert set(digest) <= set("0123456789abcdef")
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["average_estimated_half_life_seconds"] == "11255.000000"
    assert payload["rows"][0]["event_domain"] == "macro-data"
    assert payload["rows"][1]["estimated_half_life_seconds"] == "18720.000000"
    assert not any(isinstance(value, float) for value in _walk_payload_values(payload))
    assert ": 0.5" not in encoded

    encoded_keys = encoded.lower()
    assert "event_id" not in encoded_keys
    assert "market_slug" not in encoded_keys
    assert "source_id" not in encoded_keys


def test_validation_rejects_bad_numeric_types_domains_times_statuses_and_flags() -> None:
    with pytest.raises(ValueError, match="source_update_weight"):
        config(source_update_weight=d("0.100000"))
    with pytest.raises(ValueError, match="pass_half_life_seconds"):
        config(pass_half_life_seconds=14400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="watch_half_life_seconds"):
        config(watch_half_life_seconds=_DecimalSubclass("3600"))
    with pytest.raises(ValueError, match="event_domain"):
        signal(event_domain="market-123")
    with pytest.raises(ValueError, match="aggregate_source_update_cadence_seconds"):
        signal(source_update=3600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="resolution_proximity_seconds"):
        signal(resolution_proximity=d("-1"))
    with pytest.raises(ValueError, match="generated_at"):
        report((signal(),), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at"):
        report(
            (signal(),),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="paper_only"):
        replace(signal(), paper_only=False)

    row = report((signal(),)).rows[0]
    with pytest.raises(ValueError, match="status"):
        replace(row, status="blocked")
    with pytest.raises(ValueError, match="status"):
        replace(row, status="BLOCK")


def test_public_dataclasses_are_frozen_and_manual_rows_validate_consistency() -> None:
    half_life_report = report((signal(), supplied_signal()))
    row = half_life_report.rows[0]

    with pytest.raises(FrozenInstanceError):
        half_life_report.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.estimated_half_life_seconds = d("0")  # type: ignore[misc]
    with pytest.raises(ValueError, match="estimated_half_life_seconds"):
        replace(row, estimated_half_life_seconds=d("0.000000"))
    with pytest.raises(ValueError, match="rows"):
        replace(half_life_report, rows=tuple(reversed(half_life_report.rows)))


def test_owned_module_has_no_network_db_filesystem_or_execution_surface() -> None:
    module_path = (
        Path(__file__).resolve().parents[1]
        / "src"
        / "polymarket_alpha_lab"
        / "research_event_information_half_life_report.py"
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
        "sqlite",
        "wallet",
        "auth",
        "order",
        "trade",
        "live",
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
