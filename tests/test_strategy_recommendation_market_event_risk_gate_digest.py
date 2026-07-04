from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.strategy_recommendation_market_event_risk_gate_digest"
)
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/strategy_recommendation_market_event_risk_gate_digest.py",
)
GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 4, 11, 30, tzinfo=UTC)


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
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


def cfg(**overrides: object):
    module = api()
    values = {
        "config_version": "market-event-risk-gate-v0",
        "event_risk_watch_score": d("0.400000"),
        "event_risk_block_score": d("0.700000"),
        "max_event_cluster_correlation": d("0.800000"),
        "max_market_event_dependency": d("0.750000"),
        "max_resolution_ambiguity": d("0.650000"),
        "max_source_conflict": d("0.600000"),
        "max_outcome_lag_signal": d("0.550000"),
    }
    values.update(overrides)
    return module.StrategyRecommendationMarketEventRiskGateDigestConfig(**values)


def candidate(
    candidate_id: str = "candidate-alpha",
    *,
    recommendation_id: str = "rec-alpha",
    market_slug: str = "fed-cut-september",
    selected_side: str = "yes",
    event_cluster_id: str = "macro-rates-september",
    risk_observed_at: datetime = OBSERVED_AT,
    event_cluster_correlation: Decimal = d("0.100000"),
    market_event_dependency: Decimal = d("0.120000"),
    resolution_ambiguity: Decimal = d("0.080000"),
    source_conflict: Decimal = d("0.050000"),
    outcome_lag_signal: Decimal = d("0.100000"),
    event_reference: str = "event-risk-evidence",
    reason_codes: tuple[str, ...] = ("candidate_event_risk_supplied",),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    module = api()
    return module.StrategyRecommendationMarketEventRiskGateInput(
        candidate_id=candidate_id,
        recommendation_id=recommendation_id,
        market_slug=market_slug,
        selected_side=selected_side,
        event_cluster_id=event_cluster_id,
        risk_observed_at=risk_observed_at,
        event_cluster_correlation=event_cluster_correlation,
        market_event_dependency=market_event_dependency,
        resolution_ambiguity=resolution_ambiguity,
        source_conflict=source_conflict,
        outcome_lag_signal=outcome_lag_signal,
        event_reference=event_reference,
        reason_codes=reason_codes,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def digest(*rows: object, generated_at: datetime = GENERATED_AT, config: object | None = None):
    module = api()
    return module.build_strategy_recommendation_market_event_risk_gate_digest(
        rows,
        config=config or cfg(),
        generated_at=generated_at,
    )


def assert_no_public_number_payload(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_public_number_payload(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_public_number_payload(item)


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {"rows", "reason_code_counts"}:
            continue
        if any(
            marker in field.name
            for marker in (
                "count",
                "correlation",
                "dependency",
                "ambiguity",
                "conflict",
                "lag",
                "risk_score",
                "score",
            )
        ):
            assert type(getattr(value, field.name)) is Decimal, field.name


def test_empty_input_returns_report_only_clear_decimal_digest() -> None:
    report = digest()

    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.config_version == "market-event-risk-gate-v0"
    assert report.status == "clear"
    assert report.reason_codes == ("market_event_risk_gate_clear",)
    assert report.candidate_count == d("0")
    assert report.paper_candidate_count == d("0")
    assert report.watch_candidate_count == d("0")
    assert report.blocked_candidate_count == d("0")
    assert report.max_event_risk_score == d("0.000000")
    assert report.max_event_cluster_correlation == d("0.000000")
    assert report.max_market_event_dependency == d("0.000000")
    assert report.max_resolution_ambiguity == d("0.000000")
    assert report.max_source_conflict == d("0.000000")
    assert report.max_outcome_lag_signal == d("0.000000")
    assert report.reason_code_counts == ()
    assert report.rows == ()
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert_decimal_public_numbers(report)


def test_low_event_risk_passes_paper_candidate_gate_and_payload_contract() -> None:
    module = api()
    report = digest(candidate())
    row = report.rows[0]

    assert row.gate_status == "paper_candidate"
    assert row.event_risk_score == d("0.090000")
    assert row.event_reference == "<redacted-event-risk-reference>"
    assert row.reason_codes == (
        "candidate_event_risk_supplied",
        "market_event_risk_gate_passed",
    )
    assert report.status == "clear"
    assert report.paper_candidate_count == d("1")
    assert report.reason_codes == ("market_event_risk_gate_clear",)
    assert report.reason_code_counts == (
        module.StrategyRecommendationMarketEventRiskGateReasonCodeCount(
            reason_code="candidate_event_risk_supplied",
            count=d("1"),
        ),
        module.StrategyRecommendationMarketEventRiskGateReasonCodeCount(
            reason_code="market_event_risk_gate_passed",
            count=d("1"),
        ),
    )

    payload = module.strategy_recommendation_market_event_risk_gate_digest_payload(report)
    json.dumps(payload, sort_keys=True)
    assert_no_public_number_payload(payload)
    assert payload["candidate_count"] == "1"
    assert payload["max_event_risk_score"] == "0.090000"
    assert payload["rows"][0]["event_risk_score"] == "0.090000"
    assert payload["rows"][0]["event_reference"] == "<redacted-event-risk-reference>"
    assert payload["rows"][0]["paper_only"] is True
    assert payload["rows"][0]["report_only"] is True
    assert payload["rows"][0]["readonly"] is True
    assert payload["reason_code_counts"][0]["count"] == "1"
    assert payload["reason_code_counts"][0]["paper_only"] is True
    assert payload["reason_code_counts"][0]["report_only"] is True
    assert payload["reason_code_counts"][0]["readonly"] is True


def test_watch_and_block_thresholds_combine_market_event_risk_signals() -> None:
    report = digest(
        candidate(
            "candidate-watch",
            recommendation_id="rec-watch",
            event_cluster_correlation=d("0.780000"),
            market_event_dependency=d("0.690000"),
            resolution_ambiguity=d("0.590000"),
            source_conflict=d("0.540000"),
            outcome_lag_signal=d("0.420000"),
        ),
        candidate(
            "candidate-block",
            recommendation_id="rec-block",
            event_cluster_correlation=d("0.820000"),
            market_event_dependency=d("0.760000"),
            resolution_ambiguity=d("0.660000"),
            source_conflict=d("0.620000"),
            outcome_lag_signal=d("0.580000"),
        ),
        candidate(
            "candidate-score-block",
            recommendation_id="rec-score-block",
            event_cluster_correlation=d("0.720000"),
            market_event_dependency=d("0.720000"),
            resolution_ambiguity=d("0.720000"),
            source_conflict=d("0.720000"),
            outcome_lag_signal=d("0.720000"),
        ),
    )

    assert report.status == "blocked"
    assert report.watch_candidate_count == d("1")
    assert report.blocked_candidate_count == d("2")
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-block",
        "candidate-score-block",
        "candidate-watch",
    )

    blocked = report.rows[0]
    assert blocked.gate_status == "blocked"
    assert blocked.event_risk_score == d("0.688000")
    assert blocked.reason_codes == (
        "candidate_event_risk_supplied",
        "event_cluster_correlation_blocked",
        "event_risk_score_watch",
        "market_event_dependency_blocked",
        "outcome_lag_signal_blocked",
        "resolution_ambiguity_blocked",
        "source_conflict_blocked",
    )

    score_blocked = report.rows[1]
    assert score_blocked.gate_status == "blocked"
    assert score_blocked.event_risk_score == d("0.720000")
    assert score_blocked.reason_codes == (
        "candidate_event_risk_supplied",
        "event_cluster_correlation_watch",
        "event_risk_score_blocked",
        "market_event_dependency_watch",
        "outcome_lag_signal_blocked",
        "resolution_ambiguity_blocked",
        "source_conflict_blocked",
    )

    watched = report.rows[2]
    assert watched.gate_status == "paper_watch"
    assert watched.event_risk_score == d("0.604000")
    assert watched.reason_codes == (
        "candidate_event_risk_supplied",
        "event_cluster_correlation_watch",
        "event_risk_score_watch",
        "market_event_dependency_watch",
        "outcome_lag_signal_watch",
        "resolution_ambiguity_watch",
        "source_conflict_watch",
    )

    assert report.reason_codes == (
        "event_cluster_correlation_blocked",
        "event_cluster_correlation_watch",
        "event_risk_score_blocked",
        "event_risk_score_watch",
        "market_event_dependency_blocked",
        "market_event_dependency_watch",
        "outcome_lag_signal_blocked",
        "outcome_lag_signal_watch",
        "resolution_ambiguity_blocked",
        "resolution_ambiguity_watch",
        "source_conflict_blocked",
        "source_conflict_watch",
    )


def test_rows_reason_codes_and_rollups_are_deterministic_and_unique() -> None:
    module = api()
    report = digest(
        candidate(
            "zeta",
            recommendation_id="rec-zeta",
            market_slug="zeta-market",
            source_conflict=d("0.610000"),
            reason_codes=("shared_reason",),
        ),
        candidate(
            "alpha",
            recommendation_id="rec-alpha",
            market_slug="alpha-market",
            event_cluster_correlation=d("0.760000"),
            reason_codes=("shared_reason",),
        ),
        candidate(
            "beta",
            recommendation_id="rec-beta",
            market_slug="beta-market",
            reason_codes=("beta_reason", "shared_reason"),
        ),
    )

    assert tuple(row.candidate_id for row in report.rows) == ("zeta", "alpha", "beta")
    assert report.rows[0].reason_codes == (
        "shared_reason",
        "source_conflict_blocked",
    )
    assert report.rows[1].reason_codes == (
        "event_cluster_correlation_watch",
        "shared_reason",
    )
    assert report.rows[2].reason_codes == (
        "beta_reason",
        "market_event_risk_gate_passed",
        "shared_reason",
    )
    assert all(len(row.reason_codes) == len(set(row.reason_codes)) for row in report.rows)
    assert report.reason_code_counts == (
        module.StrategyRecommendationMarketEventRiskGateReasonCodeCount(
            reason_code="shared_reason",
            count=d("3"),
        ),
        module.StrategyRecommendationMarketEventRiskGateReasonCodeCount(
            reason_code="beta_reason",
            count=d("1"),
        ),
        module.StrategyRecommendationMarketEventRiskGateReasonCodeCount(
            reason_code="event_cluster_correlation_watch",
            count=d("1"),
        ),
        module.StrategyRecommendationMarketEventRiskGateReasonCodeCount(
            reason_code="market_event_risk_gate_passed",
            count=d("1"),
        ),
        module.StrategyRecommendationMarketEventRiskGateReasonCodeCount(
            reason_code="source_conflict_blocked",
            count=d("1"),
        ),
    )


def test_utc_aware_datetimes_only_and_offsets_normalize_to_utc() -> None:
    offset_time = datetime(
        2026,
        7,
        4,
        7,
        30,
        tzinfo=timezone(timedelta(hours=-4)),
    )
    report = digest(
        candidate(risk_observed_at=offset_time),
        generated_at=datetime(2026, 7, 4, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert report.generated_at == GENERATED_AT
    assert report.rows[0].risk_observed_at == OBSERVED_AT

    with pytest.raises(ValueError, match="risk_observed_at"):
        candidate(risk_observed_at=datetime(2026, 7, 4, 11, 30))
    with pytest.raises(ValueError, match="generated_at"):
        digest(candidate(), generated_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="risk_observed_at"):
        candidate(
            risk_observed_at=datetime(2026, 7, 4, 11, 30, tzinfo=_NoneOffsetTz()),
        )
    with pytest.raises(ValueError, match="generated_at"):
        digest(
            candidate(),
            generated_at=_DatetimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )


def test_public_dataclasses_are_frozen_decimal_only_and_validate_flags() -> None:
    module = api()

    for exported_name in module.__all__:
        exported = getattr(module, exported_name)
        if isinstance(exported, type):
            assert is_dataclass(exported)
            assert exported.__dataclass_params__.frozen is True

    report = digest(candidate())
    row = report.rows[0]
    reason_count = report.reason_code_counts[0]

    with pytest.raises(FrozenInstanceError):
        report.status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        row.gate_status = "blocked"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(candidate(), paper_only=False)
    with pytest.raises(ValueError, match="report_only"):
        replace(row, report_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="paper_only"):
        replace(reason_count, paper_only=False)

    for value in (cfg(), candidate(), row, reason_count, report):
        assert_decimal_public_numbers(value)

    with pytest.raises(ValueError, match="event_cluster_correlation"):
        candidate(event_cluster_correlation=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="source_conflict"):
        candidate(source_conflict=0.5)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="outcome_lag_signal"):
        candidate(outcome_lag_signal=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="max_source_conflict"):
        cfg(max_source_conflict=1)  # type: ignore[arg-type]


def test_validation_errors_reject_bad_inputs_and_inconsistent_manual_reports() -> None:
    module = api()

    with pytest.raises(ValueError, match="selected_side"):
        candidate(selected_side="maybe")
    with pytest.raises(ValueError, match="event_cluster_id"):
        candidate(event_cluster_id="")
    with pytest.raises(ValueError, match="event_risk_watch_score"):
        cfg(event_risk_watch_score=d("0.710000"))
    with pytest.raises(ValueError, match="reason_codes"):
        candidate(reason_codes=("same_reason", "same_reason"))
    with pytest.raises(ValueError, match="candidates"):
        module.build_strategy_recommendation_market_event_risk_gate_digest(
            "bad",
            config=cfg(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="duplicate recommendation_id"):
        digest(candidate(), candidate(candidate_id="candidate-beta"))
    with pytest.raises(ValueError, match="config must be"):
        module.build_strategy_recommendation_market_event_risk_gate_digest(
            (),
            config=object(),
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="report must be"):
        module.strategy_recommendation_market_event_risk_gate_digest_payload(object())

    report = digest(candidate())
    with pytest.raises(ValueError, match="candidate_count"):
        replace(report, candidate_count=d("2"))
    with pytest.raises(ValueError, match="rows"):
        replace(report, rows=())
    with pytest.raises(ValueError, match="max_event_risk_score"):
        replace(report, max_event_risk_score=d("0.500000"))
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(report, reason_code_counts=())


def test_sensitive_references_are_redacted_from_repr_payload_and_errors() -> None:
    module = api()
    secret = "postgres://agent:super-secret-token@db.example.test/polymarket"

    redacted = candidate(event_reference=secret)
    report = digest(redacted)
    payload = module.strategy_recommendation_market_event_risk_gate_digest_payload(report)
    rendered = f"{redacted!r} {report!r} {payload!r}"

    assert redacted.event_reference == "<redacted-event-risk-reference>"
    assert report.rows[0].event_reference == "<redacted-event-risk-reference>"
    assert payload["rows"][0]["event_reference"] == "<redacted-event-risk-reference>"
    assert secret not in rendered
    assert "secret-token" not in rendered.lower()

    with pytest.raises(ValueError) as exc:
        candidate(candidate_id=secret)
    assert "candidate_id" in str(exc.value)
    assert secret not in str(exc.value)
    assert "secret-token" not in str(exc.value).lower()


def test_module_source_is_pure_report_only_without_runtime_surface() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    lowered = source.lower()

    for forbidden in (
        "live",
        "trading",
        "auth",
        "wallet",
        "broker",
        "order",
        "cancel",
        "replace",
        "private_key",
        "api_key",
        "requests",
        "httpx",
        "aiohttp",
        "socket",
        "websocket",
        "sqlite",
        "psycopg",
        "supabase",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered

    tree = ast.parse(source)
    forbidden_imports = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write",
        "write_text",
        "write_bytes",
    }
    for node in ast.walk(tree):
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        elif isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".", 1)[0] not in forbidden_imports
        elif isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in {"float", "open", "__import__"}
            elif isinstance(func, ast.Attribute):
                assert func.attr not in forbidden_calls
