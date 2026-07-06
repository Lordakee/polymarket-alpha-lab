from __future__ import annotations

import ast
import importlib
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = "polymarket_alpha_lab.strategy_candidate_time_to_catalyst_rank_v2"
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "strategy_candidate_time_to_catalyst_rank_v2.py"
)
GENERATED_AT = datetime(2026, 7, 6, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 6, 10, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        if exc.name == MODULE_NAME:
            pytest.fail(f"missing time-to-catalyst rank module: {MODULE_NAME}")
        raise


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "maximum_catalyst_window_days": d("30.000000"),
        "near_term_window_days": d("7.000000"),
        "base_score_weight": d("0.600000"),
        "relevance_score_weight": d("0.250000"),
        "timing_score_weight": d("0.150000"),
        "near_term_catalyst_boost": d("0.150000"),
        "stale_catalyst_penalty": d("0.350000"),
    }
    values.update(overrides)
    return module.StrategyCandidateTimeToCatalystRankV2Config(**values)


def candidate(
    candidate_id: str = "candidate-alpha",
    *,
    market_slug: str = "fed-cuts-september",
    event_id: str = "macro-rates-2026",
    catalyst_reference: str = "fomc-statement",
    observed_at: datetime = OBSERVED_AT,
    catalyst_at: datetime = GENERATED_AT + timedelta(days=2),
    base_research_score: Decimal = d("0.700000"),
    catalyst_relevance_score: Decimal = d("0.900000"),
    evidence_freshness_score: Decimal = d("0.800000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.StrategyCandidateTimeToCatalystRankV2Candidate(
        candidate_id=candidate_id,
        market_slug=market_slug,
        event_id=event_id,
        catalyst_reference=catalyst_reference,
        observed_at=observed_at,
        catalyst_at=catalyst_at,
        base_research_score=base_research_score,
        catalyst_relevance_score=catalyst_relevance_score,
        evidence_freshness_score=evidence_freshness_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: object, **overrides: object) -> Any:
    module = api()
    generated_at = overrides.pop("generated_at", GENERATED_AT)
    selected_config = overrides.pop("config", None)
    if overrides:
        raise AssertionError(f"unexpected overrides: {sorted(overrides)}")
    return module.build_strategy_candidate_time_to_catalyst_rank_v2(
        items,
        config=selected_config or config(),
        generated_at=generated_at,
    )


def payload_values(value: Any) -> tuple[Any, ...]:
    values: list[Any] = [value]
    if isinstance(value, dict):
        for item in value.values():
            values.extend(payload_values(item))
    if isinstance(value, list):
        for item in value:
            values.extend(payload_values(item))
    return tuple(values)


def test_time_to_catalyst_ranking_prefers_highest_score_then_nearest_date() -> None:
    report = build_report(
        candidate(
            "candidate-later",
            catalyst_reference="inflation-print",
            catalyst_at=GENERATED_AT + timedelta(days=20),
            base_research_score=d("0.800000"),
            catalyst_relevance_score=d("0.900000"),
        ),
        candidate(
            "candidate-near",
            catalyst_reference="policy-meeting",
            catalyst_at=GENERATED_AT + timedelta(days=2),
            base_research_score=d("0.700000"),
            catalyst_relevance_score=d("0.900000"),
        ),
        candidate(
            "candidate-tie",
            catalyst_reference="jobs-report",
            catalyst_at=GENERATED_AT + timedelta(days=2),
            base_research_score=d("0.700000"),
            catalyst_relevance_score=d("0.900000"),
        ),
    )

    assert report.catalyst_rank_status == "ranked"
    assert report.candidate_count == d("3")
    assert tuple(row.candidate_id for row in report.rows) == (
        "candidate-near",
        "candidate-tie",
        "candidate-later",
    )
    assert tuple(row.catalyst_rank for row in report.rows) == (d("1"), d("2"), d("3"))
    assert report.top_candidate_id == "candidate-near"
    assert report.rows[0].days_to_catalyst == d("2.000000")
    assert report.rows[0].catalyst_rank_score > report.rows[2].catalyst_rank_score


def test_near_term_catalyst_boosts_and_stale_catalysts_are_penalized() -> None:
    report = build_report(
        candidate(
            "candidate-stale",
            catalyst_reference="past-hearing",
            catalyst_at=GENERATED_AT - timedelta(days=1),
            base_research_score=d("0.990000"),
            catalyst_relevance_score=d("1.000000"),
        ),
        candidate(
            "candidate-near",
            catalyst_reference="near-hearing",
            catalyst_at=GENERATED_AT + timedelta(days=3),
            base_research_score=d("0.650000"),
            catalyst_relevance_score=d("0.800000"),
        ),
        candidate(
            "candidate-distant",
            catalyst_reference="annual-meeting",
            catalyst_at=GENERATED_AT + timedelta(days=45),
            base_research_score=d("0.900000"),
            catalyst_relevance_score=d("0.900000"),
        ),
    )

    by_id = {row.candidate_id: row for row in report.rows}
    near = by_id["candidate-near"]
    stale = by_id["candidate-stale"]
    distant = by_id["candidate-distant"]

    assert near.catalyst_status == "near_term"
    assert near.near_term_boost == d("0.150000")
    assert "near_term_catalyst_boost" in near.reason_codes
    assert stale.catalyst_status == "stale"
    assert stale.stale_penalty == d("0.350000")
    assert stale.reason_codes == ("stale_catalyst_penalty",)
    assert distant.catalyst_status == "out_of_window"
    assert distant.timing_score == d("0.000000")
    assert report.near_term_candidate_count == d("1")
    assert report.stale_candidate_count == d("1")
    assert "stale_catalyst_penalty" in report.reason_codes


def test_serialization_uses_decimal_strings_and_payload_bound_digest() -> None:
    eastern = timezone(timedelta(hours=-4))
    report = build_report(
        candidate(
            observed_at=datetime(2026, 7, 6, 6, 0, tzinfo=eastern),
            catalyst_at=datetime(2026, 7, 8, 8, 0, tzinfo=eastern),
        ),
    )

    payload = report.payload

    assert payload["candidate_count"] == "1"
    assert payload["top_catalyst_rank_score"] == report.top_catalyst_rank_score.to_eng_string()
    assert payload["generated_at"] == "2026-07-06T12:00:00+00:00"
    assert payload["rows"][0]["observed_at"] == "2026-07-06T10:00:00+00:00"
    assert payload["rows"][0]["days_to_catalyst"] == "2.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert not any(type(value) is Decimal for value in payload_values(payload))
    assert not any(type(value) is float for value in payload_values(payload))

    module = api()
    assert module.strategy_candidate_time_to_catalyst_rank_v2_payload(report) == payload
    assert module.strategy_candidate_time_to_catalyst_rank_v2_payload(payload) == payload


def test_empty_report_is_readonly_report_only_and_digest_backed() -> None:
    report = build_report()

    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.catalyst_rank_status == "empty"
    assert report.candidate_count == d("0")
    assert report.near_term_candidate_count == d("0")
    assert report.stale_candidate_count == d("0")
    assert report.top_candidate_id is None
    assert report.top_catalyst_rank_score is None
    assert report.average_days_to_catalyst == d("0.000000")
    assert report.reason_codes == ("no_catalyst_candidates",)
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_dataclasses_are_frozen_decimal_only_and_hard_flagged() -> None:
    module = api()
    sample_config = config()
    sample_candidate = candidate()
    report = build_report(sample_candidate)
    row = report.rows[0]

    decimal_fields = {
        "maximum_catalyst_window_days",
        "near_term_window_days",
        "base_score_weight",
        "relevance_score_weight",
        "timing_score_weight",
        "near_term_catalyst_boost",
        "stale_catalyst_penalty",
        "base_research_score",
        "catalyst_relevance_score",
        "evidence_freshness_score",
        "days_to_catalyst",
        "timing_score",
        "near_term_boost",
        "stale_penalty",
        "catalyst_rank_score",
        "catalyst_rank",
        "candidate_count",
        "near_term_candidate_count",
        "stale_candidate_count",
        "top_catalyst_rank_score",
        "average_days_to_catalyst",
    }

    for item in (sample_config, sample_candidate, row, report):
        assert is_dataclass(item)
        assert item.paper_only is True
        assert item.report_only is True
        assert item.readonly is True
        with pytest.raises(FrozenInstanceError):
            item.readonly = False  # type: ignore[misc]
        for field in fields(item):
            value = getattr(item, field.name)
            if field.name in decimal_fields and value is not None:
                assert type(value) is Decimal

    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(sample_config, paper_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        module.StrategyCandidateTimeToCatalystRankV2Candidate(
            **{
                **sample_candidate.payload,
                "observed_at": sample_candidate.observed_at,
                "catalyst_at": sample_candidate.catalyst_at,
                "readonly": False,
            },
        )


@pytest.mark.parametrize(
    ("field_name", "bad_value", "message"),
    (
        (
            "base_research_score",
            _DecimalSubclass("0.700000"),
            "base_research_score must be exactly Decimal",
        ),
        (
            "catalyst_relevance_score",
            0.9,
            "catalyst_relevance_score must be exactly Decimal",
        ),
        (
            "evidence_freshness_score",
            d("1.000001"),
            "evidence_freshness_score must be <= 1.000000",
        ),
    ),
)
def test_candidate_validation_rejects_non_decimal_and_out_of_range_values(
    field_name: str,
    bad_value: object,
    message: str,
) -> None:
    with pytest.raises(ValueError, match=message):
        candidate(**{field_name: bad_value})


def test_config_validation_rejects_bad_thresholds_datetime_and_flags() -> None:
    module = api()

    with pytest.raises(ValueError, match="near_term_window_days"):
        config(near_term_window_days=d("31.000000"))
    with pytest.raises(ValueError, match="maximum_catalyst_window_days must be >"):
        config(maximum_catalyst_window_days=d("0.000000"))
    with pytest.raises(ValueError, match="observed_at must be exactly datetime"):
        candidate(observed_at=_DatetimeSubclass(2026, 7, 6, tzinfo=UTC))
    with pytest.raises(ValueError, match="report_only must be True"):
        module.StrategyCandidateTimeToCatalystRankV2Config(report_only=False)


def test_derived_validation_digest_rejects_tampered_reports_and_payloads() -> None:
    module = api()
    report = build_report(candidate())

    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        replace(report, candidate_count=d("9"))

    tampered_payload = dict(report.payload)
    tampered_payload["candidate_count"] = "9"
    with pytest.raises(ValueError, match="derived_validation_digest mismatch"):
        module.strategy_candidate_time_to_catalyst_rank_v2_payload(tampered_payload)


def test_unsafe_payload_keys_values_and_candidate_text_are_rejected() -> None:
    module = api()
    report = build_report(candidate())

    unsafe_key_payload = dict(report.payload)
    unsafe_key_payload["wallet_hint"] = "redacted"
    with pytest.raises(ValueError, match="unsafe public key"):
        module.strategy_candidate_time_to_catalyst_rank_v2_payload(unsafe_key_payload)

    unsafe_value_payload = dict(report.payload)
    unsafe_value_payload["operator_note"] = "requires signing"
    with pytest.raises(ValueError, match="unsafe public value"):
        module.strategy_candidate_time_to_catalyst_rank_v2_payload(unsafe_value_payload)

    unsafe_numeric_payload = dict(report.payload)
    unsafe_numeric_payload["candidate_count"] = 1
    with pytest.raises(ValueError, match="Decimal strings"):
        module.strategy_candidate_time_to_catalyst_rank_v2_payload(unsafe_numeric_payload)

    with pytest.raises(ValueError, match="unsafe public text"):
        candidate(market_slug="wallet-risk")


def test_module_exposes_no_network_persistence_or_execution_surface() -> None:
    module = api()
    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    banned_import_roots = {
        "boto3",
        "http",
        "psycopg",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "urllib",
    }
    banned_call_names = {
        "Request",
        "commit",
        "connect",
        "execute",
        "executemany",
        "open",
        "rollback",
        "urlopen",
    }
    unsafe_public_tokens = {
        "auth",
        "buy",
        "database",
        "live",
        "mutation",
        "network",
        "order",
        "persist",
        "sell",
        "signing",
        "trade",
        "wallet",
    }

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                assert alias.name.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            assert node.module.split(".")[0] not in banned_import_roots
        if isinstance(node, ast.Call):
            func = node.func
            if isinstance(func, ast.Name):
                assert func.id not in banned_call_names
            if isinstance(func, ast.Attribute):
                assert func.attr not in banned_call_names

    public_names = [name for name in dir(module) if not name.startswith("_")]
    for name in public_names:
        folded = name.lower()
        for token in unsafe_public_tokens:
            assert token not in folded
