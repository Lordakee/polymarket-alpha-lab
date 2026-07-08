from __future__ import annotations

import ast
import importlib
import importlib.util
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
MODULE_NAME = "polymarket_alpha_lab.research_team_catalyst_coverage_gap_report"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_team_catalyst_coverage_gap_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def api():
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values = {
        "min_pass_catalyst_cadence_per_week": d("3.000000"),
        "min_watch_catalyst_cadence_per_week": d("1.000000"),
        "max_pass_capacity_utilization_ratio": d("0.800000"),
        "max_watch_capacity_utilization_ratio": d("1.000000"),
        "min_pass_expertise_fit_score": d("0.750000"),
        "min_watch_expertise_fit_score": d("0.500000"),
        "max_pass_evidence_age_hours": d("24.000000"),
        "max_watch_evidence_age_hours": d("72.000000"),
        "min_pass_source_class_coverage_ratio": d("0.750000"),
        "min_watch_source_class_coverage_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchTeamCatalystCoverageGapConfig(**values)


def team_snapshot(
    specialist_team: str,
    *,
    coverage_area: str = "macro-policy",
    catalyst_class: str = "scheduled-policy",
    lookback_days: Decimal = d("7.000000"),
    observed_catalyst_count: Decimal = d("4.000000"),
    available_research_capacity: Decimal = d("4.000000"),
    active_catalyst_load: Decimal = d("2.000000"),
    expertise_fit_score: Decimal = d("0.850000"),
    latest_evidence_age_hours: Decimal = d("6.000000"),
    covered_source_class_count: Decimal = d("4.000000"),
    required_source_class_count: Decimal = d("4.000000"),
):
    module = api()
    return module.ResearchTeamCatalystCoverageGapInput(
        specialist_team=specialist_team,
        coverage_area=coverage_area,
        catalyst_class=catalyst_class,
        lookback_days=lookback_days,
        observed_catalyst_count=observed_catalyst_count,
        available_research_capacity=available_research_capacity,
        active_catalyst_load=active_catalyst_load,
        expertise_fit_score=expertise_fit_score,
        latest_evidence_age_hours=latest_evidence_age_hours,
        covered_source_class_count=covered_source_class_count,
        required_source_class_count=required_source_class_count,
    )


def report(*snapshots: object, cfg=None, generated_at: datetime = GENERATED_AT):
    module = api()
    return module.build_research_team_catalyst_coverage_gap_report(
        snapshots,
        config=cfg or config(),
        generated_at=generated_at,
    )


def test_module_contract_names_are_available() -> None:
    assert importlib.util.find_spec(MODULE_NAME) is not None


def test_gap_report_summarizes_team_catalyst_coverage_and_payload() -> None:
    module = api()

    coverage_report = report(
        team_snapshot(
            "macro-rates-team",
            coverage_area="macro-rates",
            catalyst_class="central-bank-cycle",
            observed_catalyst_count=d("4.000000"),
            active_catalyst_load=d("2.000000"),
            expertise_fit_score=d("0.850000"),
            latest_evidence_age_hours=d("6.000000"),
            covered_source_class_count=d("4.000000"),
            required_source_class_count=d("4.000000"),
        ),
        team_snapshot(
            "equity-index-team",
            coverage_area="equity-index",
            catalyst_class="earnings-cycle",
            lookback_days=d("14.000000"),
            observed_catalyst_count=d("2.000000"),
            available_research_capacity=d("3.000000"),
            active_catalyst_load=d("3.000000"),
            expertise_fit_score=d("0.650000"),
            latest_evidence_age_hours=d("48.000000"),
            covered_source_class_count=d("2.000000"),
            required_source_class_count=d("3.000000"),
        ),
        team_snapshot(
            "weather-risk-team",
            coverage_area="weather-risk",
            catalyst_class="storm-resolution",
            observed_catalyst_count=d("0.000000"),
            available_research_capacity=d("0.000000"),
            active_catalyst_load=d("2.000000"),
            expertise_fit_score=d("0.300000"),
            latest_evidence_age_hours=d("96.000000"),
            covered_source_class_count=d("0.000000"),
            required_source_class_count=d("3.000000"),
        ),
    )

    assert type(coverage_report) is module.ResearchTeamCatalystCoverageGapReport
    assert coverage_report.status == "block"
    assert coverage_report.input_count == d("3")
    assert coverage_report.gap_count == d("2")
    assert coverage_report.pass_count == d("1")
    assert coverage_report.watch_count == d("1")
    assert coverage_report.block_count == d("1")
    assert coverage_report.low_catalyst_cadence_count == d("2")
    assert coverage_report.capacity_gap_count == d("2")
    assert coverage_report.expertise_gap_count == d("2")
    assert coverage_report.stale_evidence_count == d("2")
    assert coverage_report.source_class_gap_count == d("2")
    assert coverage_report.gap_ratio == d("0.666667")
    assert coverage_report.max_gap_score == d("1.000000")
    assert coverage_report.min_catalyst_cadence_per_week == d("0.000000")
    assert coverage_report.max_capacity_utilization_ratio == d("1.000000")
    assert coverage_report.min_expertise_fit_score == d("0.300000")
    assert coverage_report.max_evidence_age_hours == d("96.000000")
    assert coverage_report.min_source_class_coverage_ratio == d("0.000000")
    assert coverage_report.reason_codes == (
        "catalyst_cadence_block",
        "team_capacity_block",
        "expertise_fit_block",
        "evidence_freshness_block",
        "source_class_coverage_block",
        "catalyst_cadence_watch",
        "team_capacity_watch",
        "expertise_fit_watch",
        "evidence_freshness_watch",
        "source_class_coverage_watch",
        "catalyst_coverage_gap_report_block",
    )

    assert tuple(row.specialist_team for row in coverage_report.rows) == (
        "weather-risk-team",
        "equity-index-team",
        "macro-rates-team",
    )
    block_row, watch_row, pass_row = coverage_report.rows
    assert block_row.status == "block"
    assert block_row.catalyst_cadence_per_week == d("0.000000")
    assert block_row.capacity_utilization_ratio == d("1.000000")
    assert block_row.source_class_coverage_ratio == d("0.000000")
    assert block_row.gap_score == d("1.000000")
    assert block_row.reason_codes == (
        "catalyst_cadence_block",
        "team_capacity_block",
        "expertise_fit_block",
        "evidence_freshness_block",
        "source_class_coverage_block",
    )
    assert watch_row.status == "watch"
    assert watch_row.catalyst_cadence_per_week == d("1.000000")
    assert watch_row.capacity_utilization_ratio == d("1.000000")
    assert watch_row.source_class_coverage_ratio == d("0.666667")
    assert watch_row.gap_score == d("0.500000")
    assert watch_row.reason_codes == (
        "catalyst_cadence_watch",
        "team_capacity_watch",
        "expertise_fit_watch",
        "evidence_freshness_watch",
        "source_class_coverage_watch",
    )
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ()

    payload = module.research_team_catalyst_coverage_gap_report_payload(coverage_report)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["input_count"] == "3"
    assert payload["gap_ratio"] == "0.666667"
    assert payload["rows"][0]["capacity_utilization_ratio"] == "1.000000"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["derived_validation_digest"] == coverage_report.derived_validation_digest
    assert len(payload["derived_validation_digest"]) == 64
    assert module.validate_research_team_catalyst_coverage_gap_public_payload(payload)
    assert_no_numeric_payload(payload)
    assert_no_raw_identifier_surface(payload)
    assert_no_action_language(payload)
    json.dumps(payload, allow_nan=False, sort_keys=True)


def test_payload_and_digest_are_deterministic_across_input_sequence() -> None:
    module = api()
    snapshots = (
        team_snapshot("zeta-team", coverage_area="zeta", catalyst_class="weekly-cycle"),
        team_snapshot(
            "alpha-team",
            coverage_area="alpha",
            catalyst_class="monthly-cycle",
            observed_catalyst_count=d("0.000000"),
            available_research_capacity=d("0.000000"),
            active_catalyst_load=d("2.000000"),
            expertise_fit_score=d("0.250000"),
            latest_evidence_age_hours=d("100.000000"),
            covered_source_class_count=d("0.000000"),
            required_source_class_count=d("2.000000"),
        ),
        team_snapshot(
            "middle-team",
            coverage_area="middle",
            catalyst_class="quarterly-cycle",
            observed_catalyst_count=d("2.000000"),
            active_catalyst_load=d("4.000000"),
            latest_evidence_age_hours=d("36.000000"),
            covered_source_class_count=d("2.000000"),
            required_source_class_count=d("3.000000"),
        ),
    )

    first = report(*snapshots)
    second = report(*reversed(snapshots))

    assert tuple(row.specialist_team for row in first.rows) == (
        "alpha-team",
        "middle-team",
        "zeta-team",
    )
    assert first.derived_validation_digest == second.derived_validation_digest
    assert module.research_team_catalyst_coverage_gap_report_payload(
        first,
    ) == module.research_team_catalyst_coverage_gap_report_payload(second)


def test_timezone_normalization_and_empty_input_status() -> None:
    eastern = timezone(timedelta(hours=-4))

    coverage_report = report(
        team_snapshot("timezone-team"),
        generated_at=datetime(2026, 7, 8, 8, 0, tzinfo=eastern),
    )

    assert coverage_report.generated_at == GENERATED_AT
    payload = api().research_team_catalyst_coverage_gap_report_payload(coverage_report)
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert_no_numeric_payload(payload)

    empty_report = report()
    assert empty_report.status == "block"
    assert empty_report.input_count == d("0")
    assert empty_report.gap_ratio is None
    assert empty_report.min_catalyst_cadence_per_week is None
    assert empty_report.max_capacity_utilization_ratio is None
    assert empty_report.reason_codes == ("catalyst_coverage_gap_report_no_inputs",)
    assert api().validate_research_team_catalyst_coverage_gap_public_payload(
        api().research_team_catalyst_coverage_gap_report_payload(empty_report),
    )


def test_dataclasses_are_frozen_exact_decimal_hard_flagged_and_digest_bound() -> None:
    module = api()

    for klass in (
        module.ResearchTeamCatalystCoverageGapConfig,
        module.ResearchTeamCatalystCoverageGapInput,
        module.ResearchTeamCatalystCoverageGapReasonCodeCount,
        module.ResearchTeamCatalystCoverageGapRow,
        module.ResearchTeamCatalystCoverageGapReport,
    ):
        assert is_dataclass(klass)
        assert klass.__dataclass_params__.frozen is True

    with pytest.raises(ValueError, match="min_pass_catalyst_cadence_per_week"):
        config(min_pass_catalyst_cadence_per_week=3)
    with pytest.raises(ValueError, match="min_watch_expertise_fit_score"):
        config(min_watch_expertise_fit_score=_DecimalSubclass("0.500000"))
    with pytest.raises(ValueError, match="observed_catalyst_count"):
        team_snapshot("bad-decimal-team", observed_catalyst_count=4)  # type: ignore[arg-type]

    input_row = team_snapshot("frozen-team")
    with pytest.raises(FrozenInstanceError):
        input_row.specialist_team = "changed"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(input_row, paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        config(report_only=False)

    good_report = report(input_row)
    with pytest.raises(FrozenInstanceError):
        good_report.status = "block"  # type: ignore[misc]
    with pytest.raises(ValueError, match="readonly"):
        replace(good_report, readonly=False)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(good_report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="input_count"):
        replace(good_report, input_count=1)

    decimal_or_optional_decimal_fields = {
        "input_count",
        "gap_count",
        "pass_count",
        "watch_count",
        "block_count",
        "low_catalyst_cadence_count",
        "capacity_gap_count",
        "expertise_gap_count",
        "stale_evidence_count",
        "source_class_gap_count",
        "gap_ratio",
        "max_gap_score",
        "min_catalyst_cadence_per_week",
        "max_capacity_utilization_ratio",
        "min_expertise_fit_score",
        "max_evidence_age_hours",
        "min_source_class_coverage_ratio",
    }
    for field in fields(good_report):
        if field.name in decimal_or_optional_decimal_fields:
            assert getattr(good_report, field.name) is None or (
                type(getattr(good_report, field.name)) is Decimal
            )
    for row in good_report.rows:
        for field in fields(row):
            value = getattr(row, field.name)
            if field.name.endswith("_count") or field.name in {
                "lookback_days",
                "catalyst_cadence_per_week",
                "available_research_capacity",
                "active_catalyst_load",
                "capacity_utilization_ratio",
                "expertise_fit_score",
                "latest_evidence_age_hours",
                "source_class_coverage_ratio",
                "gap_score",
            }:
                assert type(value) is Decimal

    tampered = replace(good_report)
    object.__setattr__(tampered, "gap_count", d("99"))
    with pytest.raises(ValueError, match="gap_count|derived_validation_digest"):
        module.research_team_catalyst_coverage_gap_report_payload(tampered)


def test_validates_inputs_public_payload_and_unsafe_surfaces() -> None:
    module = api()

    with pytest.raises(ValueError, match="lookback_days"):
        team_snapshot("bad-lookback-team", lookback_days=d("0.000000"))
    with pytest.raises(ValueError, match="required_source_class_count"):
        team_snapshot("bad-source-coverage-team", required_source_class_count=d("0.000000"))
    with pytest.raises(ValueError, match="covered_source_class_count"):
        team_snapshot(
            "bad-covered-source-team",
            covered_source_class_count=d("5.000000"),
            required_source_class_count=d("4.000000"),
        )
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(team_snapshot("bad-generated-team"), generated_at=datetime(2026, 7, 8, 12, 0))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            team_snapshot("bad-offset-team"),
            generated_at=datetime(2026, 7, 8, 12, 0, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        module.build_research_team_catalyst_coverage_gap_report(
            (),
            config=config(),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="duplicate"):
        report(team_snapshot("duplicate-team"), team_snapshot("duplicate-team"))
    with pytest.raises(ValueError, match="unsupported"):
        config(config_version="research-team-catalyst-coverage-gap-v1")

    payload = module.research_team_catalyst_coverage_gap_report_payload(
        report(team_snapshot("payload-team")),
    )
    assert module.validate_research_team_catalyst_coverage_gap_public_payload(payload)

    with pytest.raises(ValueError, match="Decimal strings"):
        module.validate_research_team_catalyst_coverage_gap_public_payload(
            {**payload, "input_count": 1},
        )

    missing_digest = dict(payload)
    missing_digest.pop("derived_validation_digest")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_team_catalyst_coverage_gap_public_payload(missing_digest)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_team_catalyst_coverage_gap_public_payload(
            {**payload, "gap_count": "1"},
        )

    for forbidden_key in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_identifier",
        "wallet_address",
        "auth_token",
        "order_id",
        "trade_intent",
        "live_execution",
        "stake_size",
        "recommendation",
    ):
        with pytest.raises(ValueError, match="unsafe|raw identifier|action language"):
            module.validate_research_team_catalyst_coverage_gap_public_payload(
                {**payload, forbidden_key: "not allowed"},
            )


def test_module_scope_is_readonly_report_only_and_external_io_free() -> None:
    source_text = MODULE_PATH.read_text(encoding="utf-8")
    lowered_source = source_text.lower()
    for forbidden in (
        "wallet",
        "auth",
        "account",
        "broker",
        "database",
        "payload_json",
        "open(",
        "requests",
        "http",
        "network",
        "submit",
        "place",
        "persist",
        "recommend",
        "sizing",
        "position_size",
        "stake",
        "allocation",
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
    ):
        assert forbidden not in lowered_source

    tree = ast.parse(source_text)
    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call) and isinstance(node.func, ast.Name):
            assert node.func.id != "float"

    forbidden_import_fragments = (
        "db",
        "env",
        "psycopg",
        "requests",
        "socket",
        "sqlite",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )


def assert_no_numeric_payload(value: Any) -> None:
    if isinstance(value, bool) or value is None:
        return
    if isinstance(value, int | float | Decimal):
        raise AssertionError(f"numeric payload value leaked: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_payload(item)
    if isinstance(value, list | tuple):
        for item in value:
            assert_no_numeric_payload(item)


def assert_no_raw_identifier_surface(payload: dict[str, Any]) -> None:
    payload_text = repr(payload).lower()
    for forbidden in (
        "event_id",
        "market_id",
        "market_slug",
        "source_id",
        "source_identifier",
    ):
        assert forbidden not in payload_text


def assert_no_action_language(payload: dict[str, Any]) -> None:
    payload_text = repr(payload).lower()
    for forbidden in (
        "wallet",
        "auth",
        "order",
        "trade",
        "live_execution",
        "recommend",
        "sizing",
        "position_size",
        "stake",
    ):
        assert forbidden not in payload_text
