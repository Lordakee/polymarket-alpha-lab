from __future__ import annotations

import ast
import inspect
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import numbers

import pytest

import polymarket_alpha_lab.market_research_energy_pipeline_nomination_cut_digest as module
from polymarket_alpha_lab.market_research_energy_pipeline_nomination_cut_digest import (
    DEFAULT_CONFIG_VERSION,
    EnergyPipelineNominationCutDigestReport,
    EnergyPipelineNominationCutObservation,
    EnergyPipelineNominationCutThresholds,
    build_market_research_energy_pipeline_nomination_cut_digest_report,
    market_research_energy_pipeline_nomination_cut_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def observation(
    *,
    pipeline: str = "Transco Zone 4",
    region: str = "us-east",
    commodity: str = "gas",
    market_slug: str = "will-transco-zone-4-gas-flow-cut",
    observed_at: datetime = datetime(2026, 7, 4, 10, tzinfo=UTC),
    nomination_cut_percent: Decimal = d("3.000000"),
    affected_capacity: Decimal = d("50.000000"),
    storage_buffer_days: Decimal = d("8.000000"),
    demand_temperature_anomaly_f: Decimal = d("2.000000"),
    outage_duration_hours: Decimal = d("2.000000"),
    source_count: Decimal = d("3.000000"),
    source_freshness_minutes: Decimal = d("30.000000"),
    upstream_reason_codes: tuple[str, ...] = (),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> EnergyPipelineNominationCutObservation:
    return EnergyPipelineNominationCutObservation(
        pipeline=pipeline,
        region=region,
        commodity=commodity,
        market_slug=market_slug,
        observed_at=observed_at,
        nomination_cut_percent=nomination_cut_percent,
        affected_capacity=affected_capacity,
        storage_buffer_days=storage_buffer_days,
        demand_temperature_anomaly_f=demand_temperature_anomaly_f,
        outage_duration_hours=outage_duration_hours,
        source_count=source_count,
        source_freshness_minutes=source_freshness_minutes,
        upstream_reason_codes=upstream_reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: EnergyPipelineNominationCutObservation,
    generated_at: datetime = GENERATED_AT,
    thresholds: EnergyPipelineNominationCutThresholds | None = None,
):
    return build_market_research_energy_pipeline_nomination_cut_digest_report(
        observations,
        generated_at=generated_at,
        thresholds=thresholds,
    )


def test_digest_reduces_nomination_cuts_with_deterministic_counts_and_payload() -> None:
    blocked = observation(
        market_slug="will-transco-zone-4-gas-flow-cut",
        observed_at=datetime(
            2026,
            7,
            4,
            6,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
        nomination_cut_percent=d("32.500000"),
        affected_capacity=d("900.000000"),
        storage_buffer_days=d("1.000000"),
        demand_temperature_anomaly_f=d("-16.000000"),
        outage_duration_hours=d("60.000000"),
        source_count=d("1.000000"),
        source_freshness_minutes=d("240.000000"),
        upstream_reason_codes=("force_majeure", "compressor_outage"),
    )
    watch = observation(
        pipeline="Permian Highway",
        region="us-gulf",
        commodity="oil",
        market_slug="will-permian-highway-nominations-be-cut",
        nomination_cut_percent=d("12.000000"),
        affected_capacity=d("300.000000"),
        storage_buffer_days=d("2.500000"),
        demand_temperature_anomaly_f=d("9.000000"),
        outage_duration_hours=d("18.000000"),
        source_count=d("2.000000"),
        source_freshness_minutes=d("45.000000"),
        upstream_reason_codes=("scheduled_maintenance",),
    )
    clear = observation(
        pipeline="Ruby Pipeline",
        region="rockies",
        market_slug="will-ruby-pipeline-nominations-hold",
    )

    digest = report(
        clear,
        watch,
        blocked,
        generated_at=datetime(
            2026,
            7,
            4,
            8,
            tzinfo=timezone(timedelta(hours=-4)),
        ),
    )

    assert digest.generated_at == GENERATED_AT
    assert digest.config_version == DEFAULT_CONFIG_VERSION
    assert digest.phase == "phase_1_market_research"
    assert digest.status == "blocked"
    assert digest.observation_count == d("3.000000")
    assert digest.pass_count == d("1.000000")
    assert digest.watch_count == d("1.000000")
    assert digest.blocked_count == d("1.000000")
    assert digest.total_affected_capacity == d("1250.000000")
    assert digest.max_nomination_cut_percent == d("32.500000")
    assert digest.min_storage_buffer_days == d("1.000000")
    assert digest.max_demand_temperature_anomaly_f == d("16.000000")
    assert digest.max_outage_duration_hours == d("60.000000")
    assert digest.risk_score == d("1.000000")
    assert digest.average_risk_score == d("0.489444")
    assert digest.top_market_slug == "will-transco-zone-4-gas-flow-cut"
    assert tuple(row.market_slug for row in digest.rows) == (
        "will-transco-zone-4-gas-flow-cut",
        "will-permian-highway-nominations-be-cut",
        "will-ruby-pipeline-nominations-hold",
    )

    assert digest.reason_codes == (
        "nomination_cut_blocked",
        "capacity_cut_blocked",
        "storage_buffer_blocked",
        "demand_temperature_blocked",
        "outage_duration_blocked",
        "source_quorum_low",
        "source_freshness_stale",
        "nomination_cut_watch",
        "capacity_cut_watch",
        "storage_buffer_watch",
        "demand_temperature_watch",
        "outage_duration_watch",
    )
    assert digest.reason_code_counts == (
        ("nomination_cut_blocked", d("1.000000")),
        ("capacity_cut_blocked", d("1.000000")),
        ("storage_buffer_blocked", d("1.000000")),
        ("demand_temperature_blocked", d("1.000000")),
        ("outage_duration_blocked", d("1.000000")),
        ("source_quorum_low", d("1.000000")),
        ("source_freshness_stale", d("1.000000")),
        ("nomination_cut_watch", d("1.000000")),
        ("capacity_cut_watch", d("1.000000")),
        ("storage_buffer_watch", d("1.000000")),
        ("demand_temperature_watch", d("1.000000")),
        ("outage_duration_watch", d("1.000000")),
    )
    assert digest.upstream_reason_code_counts == (
        ("compressor_outage", d("1.000000")),
        ("force_majeure", d("1.000000")),
        ("scheduled_maintenance", d("1.000000")),
    )

    first_row = digest.rows[0]
    assert first_row.observed_at == datetime(2026, 7, 4, 10, tzinfo=UTC)
    assert first_row.status == "blocked"
    assert first_row.risk_score == d("1.000000")
    assert first_row.upstream_reason_codes == ("compressor_outage", "force_majeure")
    assert first_row.paper_only is True
    assert first_row.report_only is True
    assert first_row.readonly is True

    payload = market_research_energy_pipeline_nomination_cut_digest_payload(digest)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-04T12:00:00+00:00"
    assert payload["observation_count"] == "3.000000"
    assert payload["risk_score"] == "1.000000"
    assert payload["average_risk_score"] == "0.489444"
    assert payload["thresholds"]["blocked_nomination_cut_percent"] == "25.000000"
    assert payload["rows"][0]["nomination_cut_percent"] == "32.500000"
    assert payload["rows"][0]["observed_at"] == "2026-07-04T10:00:00+00:00"
    assert payload["reason_code_counts"][0] == [
        "nomination_cut_blocked",
        "1.000000",
    ]


def test_empty_and_all_pass_reports_use_pass_status_and_canonical_payload() -> None:
    empty = report()

    assert empty.status == "pass"
    assert empty.observation_count == d("0.000000")
    assert empty.reason_codes == ("energy_pipeline_nomination_cut_no_observations",)
    assert empty.reason_code_counts == (
        ("energy_pipeline_nomination_cut_no_observations", d("1.000000")),
    )
    assert empty.rows == ()
    assert empty.top_market_slug is None

    clear = report(
        observation(market_slug="clear-a"),
        observation(
            pipeline="Trailblazer",
            region="midcontinent",
            market_slug="clear-b",
        ),
    )

    assert clear.status == "pass"
    assert clear.pass_count == d("2.000000")
    assert clear.watch_count == d("0.000000")
    assert clear.blocked_count == d("0.000000")
    assert clear.reason_codes == ("energy_pipeline_nomination_cut_passed",)
    assert clear.reason_code_counts == (
        ("energy_pipeline_nomination_cut_passed", d("2.000000")),
    )
    assert market_research_energy_pipeline_nomination_cut_digest_payload(clear)[
        "pass_count"
    ] == "2.000000"


def test_risk_threshold_only_blocked_rows_get_explicit_reason_code() -> None:
    thresholds = EnergyPipelineNominationCutThresholds(
        watch_risk_score=d("0.100000"),
        blocked_risk_score=d("0.200000"),
    )

    digest = report(
        observation(
            market_slug="risk-only-blocked",
            nomination_cut_percent=d("9.000000"),
            affected_capacity=d("240.000000"),
            storage_buffer_days=d("3.100000"),
            demand_temperature_anomaly_f=d("7.500000"),
            outage_duration_hours=d("11.000000"),
        ),
        thresholds=thresholds,
    )

    assert digest.status == "blocked"
    assert digest.blocked_count == d("1.000000")
    assert digest.rows[0].status == "blocked"
    assert digest.rows[0].risk_score == d("0.262917")
    assert digest.rows[0].reason_codes == ("risk_score_blocked",)
    assert digest.reason_codes == ("risk_score_blocked",)
    assert digest.reason_code_counts == (("risk_score_blocked", d("1.000000")),)


def test_validation_enforces_frozen_flags_decimal_datetime_and_row_invariants() -> None:
    digest = report(
        observation(
            nomination_cut_percent=d("32.000000"),
            affected_capacity=d("800.000000"),
        ),
    )

    assert is_dataclass(digest)
    assert digest.__dataclass_params__.frozen is True
    with pytest.raises(FrozenInstanceError):
        digest.status = "pass"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        digest.rows[0].status = "pass"  # type: ignore[misc]

    with pytest.raises(ValueError, match="timezone-aware"):
        observation(observed_at=datetime(2026, 7, 4, 10))
    with pytest.raises(ValueError, match="Decimal"):
        observation(nomination_cut_percent=12)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        observation(affected_capacity=1.2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="six decimal"):
        observation(storage_buffer_days=d("1.0000001"))
    with pytest.raises(ValueError, match="integer Decimal"):
        observation(source_count=d("1.500000"))
    with pytest.raises(ValueError, match="commodity"):
        observation(commodity="power")
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)  # type: ignore[call-arg]
    with pytest.raises(ValueError, match="report_only"):
        EnergyPipelineNominationCutThresholds(report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(digest, readonly=False)

    with pytest.raises(ValueError, match="status"):
        replace(digest.rows[0], status="pass")
    with pytest.raises(ValueError, match="reason_codes"):
        replace(digest.rows[0], reason_codes=("energy_pipeline_nomination_cut_passed",))
    with pytest.raises(ValueError, match="status"):
        replace(digest.rows[0], reason_codes=("source_quorum_low",))
    with pytest.raises(ValueError, match="observation_count"):
        replace(digest, observation_count=d("2.000000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            digest,
            reason_code_counts=(("nomination_cut_blocked", d("2.000000")),),
        )

    public_instances = (
        EnergyPipelineNominationCutThresholds(),
        observation(),
        digest.rows[0],
        digest,
    )
    for instance in public_instances:
        for field in fields(type(instance)):
            value = getattr(instance, field.name)
            if isinstance(value, numbers.Number) and type(value) is not bool:
                assert type(value) is Decimal, f"{type(instance).__name__}.{field.name}"


def test_payload_rejects_float_int_flag_downgrades_and_unsafe_surface_names() -> None:
    with pytest.raises(ValueError, match="float"):
        market_research_energy_pipeline_nomination_cut_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "risk_score": 0.5,
            },
        )

    with pytest.raises(ValueError, match="Decimal"):
        market_research_energy_pipeline_nomination_cut_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "observation_count": 1,
            },
        )

    with pytest.raises(ValueError, match="report_only"):
        market_research_energy_pipeline_nomination_cut_digest_payload(
            {
                "paper_only": True,
                "report_only": False,
                "readonly": True,
            },
        )

    with pytest.raises(ValueError, match="unsafe live surface"):
        market_research_energy_pipeline_nomination_cut_digest_payload(
            {
                "paper_only": True,
                "report_only": True,
                "readonly": True,
                "wallet": "blocked",
            },
        )

    with pytest.raises(ValueError, match="EnergyPipelineNominationCutDigestReport"):
        market_research_energy_pipeline_nomination_cut_digest_payload("bad input")


def test_public_surface_is_pure_report_only_and_omits_forbidden_terms() -> None:
    source = inspect.getsource(module)
    lowered_source = source.lower()
    tree = ast.parse(source)

    assert module.__all__ == (
        "DEFAULT_CONFIG_VERSION",
        "PHASE_NAME",
        "EnergyPipelineNominationCutDigestReport",
        "EnergyPipelineNominationCutDigestRow",
        "EnergyPipelineNominationCutObservation",
        "EnergyPipelineNominationCutThresholds",
        "build_market_research_energy_pipeline_nomination_cut_digest_report",
        "market_research_energy_pipeline_nomination_cut_digest_payload",
    )
    assert EnergyPipelineNominationCutDigestReport.__dataclass_params__.frozen is True

    forbidden_attributes = (
        "connect",
        "client",
        "session",
        "sign",
        "submit",
        "cancel",
        "replace",
        "mutation",
        "exchange",
    )
    assert all(not hasattr(module, name) for name in forbidden_attributes)

    forbidden_source_terms = (
        "live trading",
        "wallet",
        "private_key",
        "api_key",
        "database",
        "supabase",
        "postgres",
        "requests",
        "httpx",
        "socket",
        "urlopen",
        "psycopg",
    )
    assert not any(term in lowered_source for term in forbidden_source_terms)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "db",
        "env",
        "cli",
        "psycopg",
        "requests",
        "httpx",
        "socket",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )
