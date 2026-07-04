import ast
import inspect
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal

import pytest

from polymarket_alpha_lab import (
    strategy_recommendation_resolution_risk_triage as triage_module,
)
from polymarket_alpha_lab.strategy_recommendation_resolution_risk_triage import (
    StrategyRecommendationResolutionRiskCandidate,
    StrategyRecommendationResolutionRiskTriageConfig,
    StrategyRecommendationResolutionRiskTriageReport,
    build_strategy_recommendation_resolution_risk_triage_report,
    strategy_recommendation_resolution_risk_triage_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
CLOSES_AT = datetime(2026, 7, 5, 12, 0, tzinfo=UTC)
EVIDENCE_AT = GENERATED_AT - timedelta(hours=6)


class _NoOffsetTimezone(tzinfo):
    def utcoffset(self, dt):
        return None

    def dst(self, dt):
        return None


def _config(**overrides) -> StrategyRecommendationResolutionRiskTriageConfig:
    values = {
        "config_version": "resolution-risk-triage-v1",
        "max_evidence_age_hours": Decimal("24.000000"),
        "close_pressure_window_hours": Decimal("12.000000"),
    }
    values.update(overrides)
    return StrategyRecommendationResolutionRiskTriageConfig(**values)


def _candidate(**overrides) -> StrategyRecommendationResolutionRiskCandidate:
    values = {
        "candidate_id": "candidate-fed-cut",
        "market_slug": "fed-cut-july-2026",
        "team_key": "macro",
        "resolution_criteria": "Resolves yes if the FOMC lowers target rates by close.",
        "resolution_criteria_ambiguous": False,
        "outcome_evidence_at": EVIDENCE_AT,
        "source_evidence_at": EVIDENCE_AT,
        "unresolved_source_conflict": False,
        "closes_at": CLOSES_AT,
        "severity_score": Decimal("0.100000"),
    }
    values.update(overrides)
    return StrategyRecommendationResolutionRiskCandidate(**values)


def _report(candidates, **config_overrides) -> StrategyRecommendationResolutionRiskTriageReport:
    return build_strategy_recommendation_resolution_risk_triage_report(
        candidates,
        config=_config(**config_overrides),
        generated_at=GENERATED_AT,
    )


def test_empty_input_returns_empty_report_without_fabricated_rows():
    report = _report(())

    assert report.triage_status == "empty"
    assert report.recommended_next_step == "collect_resolution_risk_evidence"
    assert report.candidate_count == Decimal("0")
    assert report.row_count == Decimal("0")
    assert report.clear_count == Decimal("0")
    assert report.watch_count == Decimal("0")
    assert report.blocked_count == Decimal("0")
    assert report.clear_ratio == Decimal("0.000000")
    assert report.watch_ratio == Decimal("0.000000")
    assert report.blocked_ratio == Decimal("0.000000")
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_clear_watch_and_blocked_rows_are_reduced_from_candidates():
    report = _report(
        (
            _candidate(candidate_id="clear-a", market_slug="alpha", team_key="macro"),
            _candidate(
                candidate_id="watch-a",
                market_slug="beta",
                team_key="macro",
                outcome_evidence_at=GENERATED_AT - timedelta(hours=25),
                severity_score=Decimal("0.400000"),
            ),
            _candidate(
                candidate_id="blocked-a",
                market_slug="gamma",
                team_key="ops",
                resolution_criteria_ambiguous=True,
                severity_score=Decimal("0.900000"),
            ),
        ),
    )

    assert report.triage_status == "blocked"
    assert report.recommended_next_step == "block_until_resolution_risk_repaired"
    assert report.candidate_count == Decimal("3")
    assert report.row_count == Decimal("3")
    assert report.clear_count == Decimal("1")
    assert report.watch_count == Decimal("1")
    assert report.blocked_count == Decimal("1")
    assert report.clear_ratio == Decimal("0.333333")
    assert report.watch_ratio == Decimal("0.333333")
    assert report.blocked_ratio == Decimal("0.333333")
    assert [(row.status, row.market_slug, row.team_key) for row in report.rows] == [
        ("blocked", "gamma", "ops"),
        ("watch", "beta", "macro"),
        ("clear", "alpha", "macro"),
    ]


def test_ambiguous_resolution_criteria_blocks_candidate():
    report = _report((_candidate(resolution_criteria_ambiguous=True),))

    row = report.rows[0]
    assert row.status == "blocked"
    assert row.recommended_next_step == "block_until_resolution_risk_repaired"
    assert row.reason_codes == ("ambiguous_resolution_criteria",)
    assert report.reason_code_counts[0].reason_code == "ambiguous_resolution_criteria"
    assert report.reason_code_counts[0].count == Decimal("1")


def test_stale_evidence_warns_for_outcome_and_source_timestamps():
    report = _report(
        (
            _candidate(
                outcome_evidence_at=GENERATED_AT - timedelta(hours=30),
                source_evidence_at=GENERATED_AT - timedelta(hours=31),
            ),
        ),
    )

    row = report.rows[0]
    assert row.status == "watch"
    assert row.reason_codes == (
        "stale_outcome_evidence",
        "stale_source_evidence",
    )
    assert row.outcome_evidence_age_hours == Decimal("30.000000")
    assert row.source_evidence_age_hours == Decimal("31.000000")
    assert row.hours_until_close == Decimal("72.000000")


def test_unresolved_source_conflict_blocks_candidate():
    report = _report((_candidate(unresolved_source_conflict=True),))

    row = report.rows[0]
    assert row.status == "blocked"
    assert row.reason_codes == ("unresolved_source_conflict",)
    assert report.blocked_count == Decimal("1")


def test_close_time_pressure_warns_when_candidate_is_near_close():
    report = _report(
        (
            _candidate(
                closes_at=GENERATED_AT + timedelta(hours=6),
                severity_score=Decimal("0.300000"),
            ),
        ),
    )

    row = report.rows[0]
    assert row.status == "watch"
    assert row.reason_codes == ("close_time_pressure",)
    assert row.hours_until_close == Decimal("6.000000")


def test_rows_sort_by_status_severity_market_and_team_keys():
    report = _report(
        (
            _candidate(
                candidate_id="clear-z",
                market_slug="zeta",
                team_key="team-b",
                severity_score=Decimal("0.900000"),
            ),
            _candidate(
                candidate_id="blocked-low",
                market_slug="alpha",
                team_key="team-a",
                resolution_criteria_ambiguous=True,
                severity_score=Decimal("0.100000"),
            ),
            _candidate(
                candidate_id="watch-a",
                market_slug="alpha",
                team_key="team-c",
                closes_at=GENERATED_AT + timedelta(hours=4),
                severity_score=Decimal("0.800000"),
            ),
            _candidate(
                candidate_id="blocked-high-b",
                market_slug="beta",
                team_key="team-b",
                unresolved_source_conflict=True,
                severity_score=Decimal("0.900000"),
            ),
            _candidate(
                candidate_id="blocked-high-a",
                market_slug="alpha",
                team_key="team-a",
                unresolved_source_conflict=True,
                severity_score=Decimal("0.900000"),
            ),
        ),
    )

    assert [
        (row.status, row.severity_score, row.market_slug, row.team_key)
        for row in report.rows
    ] == [
        ("blocked", Decimal("0.900000"), "alpha", "team-a"),
        ("blocked", Decimal("0.900000"), "beta", "team-b"),
        ("blocked", Decimal("0.100000"), "alpha", "team-a"),
        ("watch", Decimal("0.800000"), "alpha", "team-c"),
        ("clear", Decimal("0.900000"), "zeta", "team-b"),
    ]


def test_payload_uses_decimal_strings_utc_timestamps_and_no_float_values():
    report = _report(
        (
            _candidate(
                outcome_evidence_at=datetime(
                    2026,
                    7,
                    2,
                    2,
                    0,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                source_evidence_at=datetime(
                    2026,
                    7,
                    2,
                    3,
                    0,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
                closes_at=datetime(
                    2026,
                    7,
                    3,
                    8,
                    0,
                    tzinfo=timezone(timedelta(hours=-4)),
                ),
            ),
        ),
    )

    payload = strategy_recommendation_resolution_risk_triage_payload(report)

    assert payload["generated_at"] == "2026-07-02T12:00:00Z"
    assert payload["candidate_count"] == "1"
    assert payload["clear_ratio"] == "1.000000"
    assert payload["rows"][0]["outcome_evidence_at"] == "2026-07-02T06:00:00Z"
    assert payload["rows"][0]["source_evidence_at"] == "2026-07-02T07:00:00Z"
    assert payload["rows"][0]["closes_at"] == "2026-07-03T12:00:00Z"
    assert not _contains_float(payload)


def test_validation_errors_reject_bad_inputs_and_unsafe_flags():
    candidate = _candidate()

    with pytest.raises(ValueError, match="StrategyRecommendationResolutionRiskTriageConfig"):
        build_strategy_recommendation_resolution_risk_triage_report(
            (candidate,),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_strategy_recommendation_resolution_risk_triage_report(
            (candidate,),
            config=_config(),
            generated_at=datetime(2026, 7, 2, 12, 0),
        )
    with pytest.raises(ValueError, match="outcome_evidence_at"):
        _candidate(
            outcome_evidence_at=datetime(
                2026,
                7,
                2,
                12,
                0,
                tzinfo=_NoOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="severity_score"):
        _candidate(severity_score="0.1")
    with pytest.raises(ValueError, match="candidate_id"):
        _candidate(candidate_id=" candidate ")
    with pytest.raises(ValueError, match="resolution_criteria"):
        _candidate(resolution_criteria="")
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(candidate, readonly=False)
    with pytest.raises(ValueError, match="candidates must contain only"):
        _report((object(),))


def test_public_text_fields_reject_execution_and_secret_surfaces():
    unsafe_values = (
        ("candidate_id", "candidate-private_key"),
        ("market_slug", "wallet-refresh-market"),
        ("team_key", "auth-ops"),
        ("resolution_criteria", "Cancel order if source text changes."),
    )

    for field_name, unsafe_value in unsafe_values:
        with pytest.raises(ValueError, match=field_name):
            _candidate(**{field_name: unsafe_value})


def test_public_dataclasses_are_frozen():
    report = _report((_candidate(),))

    with pytest.raises(FrozenInstanceError):
        report.triage_status = "blocked"
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "blocked"


def test_public_numeric_fields_are_decimal_only():
    config = _config()
    candidate = _candidate()
    report = _report((candidate,), close_pressure_window_hours=Decimal("96.000000"))

    decimal_fields_by_object = (
        (config, ("max_evidence_age_hours", "close_pressure_window_hours")),
        (candidate, ("severity_score",)),
        (
            report,
            (
                "candidate_count",
                "row_count",
                "clear_count",
                "watch_count",
                "blocked_count",
                "clear_ratio",
                "watch_ratio",
                "blocked_ratio",
            ),
        ),
        (
            report.reason_code_counts[0],
            ("count",),
        ),
        (
            report.rows[0],
            (
                "severity_score",
                "outcome_evidence_age_hours",
                "source_evidence_age_hours",
                "hours_until_close",
            ),
        ),
    )

    for item, decimal_fields in decimal_fields_by_object:
        for field_name in decimal_fields:
            assert type(getattr(item, field_name)) is Decimal
        for field_name, value in item.__dict__.items():
            assert type(value) not in (int, float), field_name


def test_triage_module_stays_pure_report_only_and_without_forbidden_surfaces():
    source = inspect.getsource(triage_module)
    tree = ast.parse(source)
    imported_modules: set[str] = set()
    call_names: set[str] = set()
    float_literals: list[float] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        elif isinstance(node, ast.Call):
            function = node.func
            if isinstance(function, ast.Name):
                call_names.add(function.id)
            elif isinstance(function, ast.Attribute):
                call_names.add(function.attr)
        elif isinstance(node, ast.Constant) and isinstance(node.value, float):
            float_literals.append(node.value)

    forbidden_imports = {
        "os",
        "pathlib",
        "subprocess",
        "requests",
        "httpx",
        "urllib",
        "sqlite3",
        "psycopg",
        "polymarket_alpha_lab.cli",
        "polymarket_alpha_lab.runner",
        "polymarket_alpha_lab.paper_execution",
        "polymarket_alpha_lab.paper_broker",
    }
    forbidden_calls = {
        "connect",
        "cursor",
        "execute",
        "executemany",
        "commit",
        "rollback",
        "open",
        "urlopen",
        "submit_order",
        "cancel_order",
        "sign_order",
        "place_order",
        "replace",
    }
    forbidden_fragments = (
        "live",
        "auth",
        "wallet",
        "order",
        "cancel",
        "replace",
        "private_key",
        "private-key",
        "broker",
        "order_submission",
        "submit_order",
        "cancel_order",
        "signing",
        "investment_advice",
    )

    assert imported_modules.isdisjoint(forbidden_imports)
    assert call_names.isdisjoint(forbidden_calls)
    assert float_literals == []
    assert all(fragment not in source.lower() for fragment in forbidden_fragments)


def _contains_float(value) -> bool:
    if isinstance(value, float):
        return True
    if isinstance(value, dict):
        return any(_contains_float(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float(item) for item in value)
    return False
