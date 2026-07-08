from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab.research_strategy_candidate_cluster_risk_report import (
    DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_RISK_REPORT_CONFIG_VERSION,
    ResearchStrategyCandidateClusterRiskAggregate,
    ResearchStrategyCandidateClusterRiskCandidate,
    ResearchStrategyCandidateClusterRiskConfig,
    ResearchStrategyCandidateClusterRiskReasonCodeCount,
    ResearchStrategyCandidateClusterRiskReport,
    build_research_strategy_candidate_cluster_risk_report,
    research_strategy_candidate_cluster_risk_report_payload,
)


GENERATED_AT = datetime(2026, 7, 8, 13, 15, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _StringSubclass(str):
    pass


class _DecimalSubclass(Decimal):
    pass


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> ResearchStrategyCandidateClusterRiskConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_RISK_REPORT_CONFIG_VERSION
        ),
        "watch_domain_concentration_ratio": d("0.500000"),
        "block_domain_concentration_ratio": d("0.750000"),
        "watch_shared_catalyst_ratio": d("0.500000"),
        "block_shared_catalyst_ratio": d("0.750000"),
        "watch_source_overlap_ratio": d("0.500000"),
        "block_source_overlap_ratio": d("0.750000"),
        "watch_settlement_ambiguity_score": d("0.300000"),
        "block_settlement_ambiguity_score": d("0.600000"),
        "watch_liquidity_cost_pressure_score": d("0.300000"),
        "block_liquidity_cost_pressure_score": d("0.600000"),
    }
    values.update(overrides)
    return ResearchStrategyCandidateClusterRiskConfig(**values)


def candidate(
    candidate_reference: str = "candidate_alpha_redacted",
    *,
    domain_bucket: str = "macro_rates",
    catalyst_bucket: str = "central_bank_window",
    source_family_buckets: tuple[str, ...] = (
        "official_rules_family",
        "scheduled_data_family",
    ),
    settlement_ambiguity_score: Decimal = d("0.100000"),
    liquidity_cost_pressure_score: Decimal = d("0.100000"),
) -> ResearchStrategyCandidateClusterRiskCandidate:
    return ResearchStrategyCandidateClusterRiskCandidate(
        candidate_reference=candidate_reference,
        domain_bucket=domain_bucket,
        catalyst_bucket=catalyst_bucket,
        source_family_buckets=source_family_buckets,
        settlement_ambiguity_score=settlement_ambiguity_score,
        liquidity_cost_pressure_score=liquidity_cost_pressure_score,
    )


def report(
    *rows: ResearchStrategyCandidateClusterRiskCandidate,
    cfg: ResearchStrategyCandidateClusterRiskConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> ResearchStrategyCandidateClusterRiskReport:
    return build_research_strategy_candidate_cluster_risk_report(
        rows,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_cluster_risk_report_blocks_aggregate_concentration_without_raw_ids() -> None:
    cluster_report = report(
        candidate(
            "candidate_zeta_redacted",
            domain_bucket="macro_rates",
            catalyst_bucket="central_bank_window",
            source_family_buckets=("official_rules_family", "scheduled_data_family"),
            settlement_ambiguity_score=d("0.700000"),
            liquidity_cost_pressure_score=d("0.500000"),
        ),
        candidate(
            "candidate_alpha_redacted",
            domain_bucket="macro_rates",
            catalyst_bucket="central_bank_window",
            source_family_buckets=("official_rules_family", "scheduled_data_family"),
            settlement_ambiguity_score=d("0.500000"),
            liquidity_cost_pressure_score=d("0.200000"),
        ),
        candidate(
            "candidate_beta_redacted",
            domain_bucket="sports_team_news",
            catalyst_bucket="injury_window",
            source_family_buckets=("official_rules_family",),
            settlement_ambiguity_score=d("0.600000"),
            liquidity_cost_pressure_score=d("0.400000"),
        ),
    )

    assert isinstance(cluster_report, ResearchStrategyCandidateClusterRiskReport)
    assert cluster_report.generated_at == GENERATED_AT
    assert cluster_report.config_version == (
        DEFAULT_RESEARCH_STRATEGY_CANDIDATE_CLUSTER_RISK_REPORT_CONFIG_VERSION
    )
    assert cluster_report.cluster_risk_status == "block"
    assert cluster_report.candidate_count == d("3.000000")
    assert cluster_report.pass_dimension_count == d("0.000000")
    assert cluster_report.watch_dimension_count == d("3.000000")
    assert cluster_report.block_dimension_count == d("2.000000")
    assert cluster_report.top_domain_concentration_ratio == d("0.666667")
    assert cluster_report.top_shared_catalyst_ratio == d("0.666667")
    assert cluster_report.top_source_overlap_ratio == d("1.000000")
    assert cluster_report.average_settlement_ambiguity_score == d("0.600000")
    assert cluster_report.average_liquidity_cost_pressure_score == d("0.366667")
    assert cluster_report.reason_codes == (
        "research_strategy_candidate_cluster_risk_domain_concentration_watch",
        "research_strategy_candidate_cluster_risk_liquidity_cost_watch",
        "research_strategy_candidate_cluster_risk_settlement_ambiguity_block",
        "research_strategy_candidate_cluster_risk_shared_catalyst_watch",
        "research_strategy_candidate_cluster_risk_source_overlap_block",
    )
    assert tuple(row.risk_status for row in cluster_report.aggregate_rows) == (
        "watch",
        "watch",
        "block",
        "block",
        "watch",
    )
    assert all(row.paper_only and row.report_only and row.readonly for row in cluster_report.aggregate_rows)
    assert cluster_report.paper_only is True
    assert cluster_report.report_only is True
    assert cluster_report.readonly is True

    payload = research_strategy_candidate_cluster_risk_report_payload(cluster_report)
    encoded_payload = json.dumps(payload, sort_keys=True)
    assert payload["candidate_count"] == "3.000000"
    assert payload["payload_digest"] == cluster_report.payload_digest
    assert cluster_report.payload_digest.startswith("sha256:")
    assert "candidate_alpha_redacted" not in encoded_payload
    assert "candidate_beta_redacted" not in encoded_payload
    assert "candidate_zeta_redacted" not in encoded_payload
    for forbidden in ("buy", "sell", "recommend", "position"):
        assert forbidden not in encoded_payload.lower()


def test_cluster_risk_report_passes_diverse_candidates_with_stable_digest() -> None:
    rows = (
        candidate(
            "candidate_delta_redacted",
            domain_bucket="macro_rates",
            catalyst_bucket="central_bank_window",
            source_family_buckets=("official_rules_family",),
        ),
        candidate(
            "candidate_alpha_redacted",
            domain_bucket="sports_team_news",
            catalyst_bucket="injury_window",
            source_family_buckets=("beat_report_family",),
            settlement_ambiguity_score=d("0.200000"),
        ),
        candidate(
            "candidate_gamma_redacted",
            domain_bucket="weather_event",
            catalyst_bucket="forecast_update_window",
            source_family_buckets=("weather_model_family",),
            liquidity_cost_pressure_score=d("0.200000"),
        ),
        candidate(
            "candidate_beta_redacted",
            domain_bucket="policy_rules",
            catalyst_bucket="court_calendar_window",
            source_family_buckets=("official_docket_family",),
        ),
    )

    first = report(*rows)
    second = report(*reversed(rows))

    assert first.cluster_risk_status == "pass"
    assert first.pass_dimension_count == d("5.000000")
    assert first.watch_dimension_count == ZERO
    assert first.block_dimension_count == ZERO
    assert first.reason_codes == ("research_strategy_candidate_cluster_risk_passed",)
    assert first.reason_code_counts == (
        ResearchStrategyCandidateClusterRiskReasonCodeCount(
            "research_strategy_candidate_cluster_risk_passed",
            d("5.000000"),
        ),
    )
    assert first.payload_digest == second.payload_digest
    assert research_strategy_candidate_cluster_risk_report_payload(first) == (
        research_strategy_candidate_cluster_risk_report_payload(second)
    )


def test_cluster_risk_report_empty_input_is_watch_with_decimal_payload() -> None:
    empty_report = report()

    assert empty_report.cluster_risk_status == "watch"
    assert empty_report.candidate_count == ZERO
    assert empty_report.reason_codes == (
        "research_strategy_candidate_cluster_risk_empty_candidate_set",
    )
    assert empty_report.reason_code_counts == (
        ResearchStrategyCandidateClusterRiskReasonCodeCount(
            "research_strategy_candidate_cluster_risk_empty_candidate_set",
            d("1.000000"),
        ),
    )
    assert tuple(row.risk_status for row in empty_report.aggregate_rows) == (
        "pass",
        "pass",
        "pass",
        "pass",
        "pass",
    )

    payload = research_strategy_candidate_cluster_risk_report_payload(empty_report)
    assert payload["candidate_count"] == "0.000000"
    assert payload["top_domain_concentration_ratio"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    json.dumps(payload, sort_keys=True)

    def walk_payload(value: object) -> None:
        if isinstance(value, dict):
            for key, child in value.items():
                assert type(key) is str
                walk_payload(child)
        elif isinstance(value, list):
            for child in value:
                walk_payload(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))
            assert type(value) is not int

    walk_payload(payload)


def test_cluster_risk_report_rejects_non_decimal_values_and_bad_datetimes() -> None:
    generated_at = datetime(2026, 7, 8, 9, 15, tzinfo=timezone(timedelta(hours=-4)))
    assert report(candidate(), generated_at=generated_at).generated_at == GENERATED_AT

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report(candidate(), generated_at=_DateTimeSubclass(2026, 7, 8, 13, 15, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(candidate(), generated_at=datetime(2026, 7, 8, 13, 15))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            candidate(),
            generated_at=datetime(2026, 7, 8, 13, 15, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="settlement_ambiguity_score must be a Decimal"):
        candidate(settlement_ambiguity_score=0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="settlement_ambiguity_score must be exactly Decimal"):
        candidate(settlement_ambiguity_score=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="watch_source_overlap_ratio must be a Decimal"):
        config(watch_source_overlap_ratio=0.5)
    with pytest.raises(ValueError, match="block_source_overlap_ratio must exceed"):
        config(
            watch_source_overlap_ratio=d("0.800000"),
            block_source_overlap_ratio=d("0.700000"),
        )
    with pytest.raises(ValueError, match="cluster_risk_status must be pass, watch, or block"):
        replace(report(candidate()), cluster_risk_status="blocked")
    with pytest.raises(ValueError, match="payload_digest must match"):
        replace(report(candidate()), payload_digest="sha256:" + "0" * 64)


def test_cluster_risk_report_freezes_records_flags_and_public_safe_inputs() -> None:
    cluster_report = report(candidate())

    for public_record in (
        config(),
        candidate(),
        cluster_report.aggregate_rows[0],
        cluster_report.reason_code_counts[0],
        cluster_report,
    ):
        assert is_dataclass(public_record)
        assert public_record.__dataclass_params__.frozen
        for field in fields(public_record):
            value = getattr(public_record, field.name)
            if (
                field.name.endswith("_ratio")
                or field.name.endswith("_score")
                or field.name.endswith("_count")
                or field.name.startswith("watch_")
                or field.name.startswith("block_")
            ):
                assert type(value) is Decimal, field.name

    with pytest.raises(FrozenInstanceError):
        cluster_report.paper_only = False  # type: ignore[misc]
    with pytest.raises(ValueError, match="config_version"):
        ResearchStrategyCandidateClusterRiskConfig(config_version=_StringSubclass("v0"))
    with pytest.raises(ValueError, match="candidate_reference must be public-safe"):
        candidate(candidate_reference="raw_event_123")
    with pytest.raises(ValueError, match="candidate_reference must be public-safe"):
        candidate(candidate_reference="market_0xabc")
    with pytest.raises(ValueError, match="source_family_buckets must be sorted"):
        candidate(source_family_buckets=("scheduled_data_family", "official_rules_family"))
    with pytest.raises(ValueError, match="unsafe public bucket"):
        candidate(source_family_buckets=("source_live_feed_family",))
    with pytest.raises(ValueError, match="candidate paper_only must be True"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="aggregate readonly must be True"):
        replace(cluster_report.aggregate_rows[0], readonly=False)
    with pytest.raises(ValueError, match="report report_only must be True"):
        replace(cluster_report, report_only=False)
    with pytest.raises(ValueError, match="candidate_reference values must be unique"):
        report(
            candidate("candidate_dupe_redacted"),
            candidate("candidate_dupe_redacted"),
        )


def test_cluster_risk_report_module_has_no_action_or_runtime_surfaces() -> None:
    module = importlib.import_module(
        "polymarket_alpha_lab.research_strategy_candidate_cluster_risk_report",
    )
    source = module.__loader__.get_source(module.__name__)
    assert source is not None
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert not isinstance(node.value, float)

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)

    forbidden_import_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "subprocess",
        "pathlib",
        "os",
        "sqlite",
        "psycopg",
        "supabase",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    lowered_source = source.lower()
    for forbidden in (
        "buy",
        "sell",
        "recommend",
        "position",
        "submit_order",
        "cancel_order",
        "replace_order",
        "create_order",
        "wallet",
        "private_key",
        "authentication",
        "database",
        "persist",
        "network",
        "urlopen",
        "connect(",
        "execute(",
    ):
        assert forbidden not in lowered_source
