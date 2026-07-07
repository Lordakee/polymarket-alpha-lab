from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, fields
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
import hashlib
import importlib
import json
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.candidate_decision_score import (
    CandidateDecisionScoreConfig,
    CandidateDecisionScoreInput,
    CandidateDecisionScoreReport,
    build_candidate_decision_score_report,
)
from polymarket_alpha_lab.candidate_decision_score_history import (
    CandidateDecisionScoreHistoryReport,
    build_candidate_decision_score_history_report,
)


MODULE_NAME = "polymarket_alpha_lab.candidate_decision_score_history_db_row"
GENERATED_AT = datetime(2026, 7, 7, 12, 30, tzinfo=UTC)
HISTORY_GENERATED_AT = datetime(2026, 7, 7, 13, 0, tzinfo=UTC)


def api() -> Any:
    try:
        return importlib.import_module(MODULE_NAME)
    except ModuleNotFoundError as exc:
        pytest.fail(f"missing candidate decision score history DB row module: {exc}")


def d(value: str) -> Decimal:
    return Decimal(value)


def _score_report(
    *,
    generated_at: datetime = GENERATED_AT,
    candidate_id: str = "candidate-alpha",
    market_id: str = "market-alpha",
    gross_edge: Decimal | None = d("0.060000"),
    evidence_score: Decimal = d("0.850000"),
) -> CandidateDecisionScoreReport:
    return build_candidate_decision_score_report(
        CandidateDecisionScoreInput(
            candidate_id=candidate_id,
            market_id=market_id,
            normalized_market_question=f"Will {candidate_id} resolve yes?",
            primary_team_id="politics",
            secondary_team_ids=("crypto_btc",),
            selected_side="yes",
            forecast_probability=d("0.620000"),
            executable_price=d("0.560000"),
            gross_edge=gross_edge,
            estimated_cost_drag=d("0.010000"),
            cost_score=d("0.800000"),
            liquidity_score=d("0.900000"),
            evidence_score=evidence_score,
            resolution_score=d("0.700000"),
            team_memory_score=d("0.750000"),
            team_memory_policy="allow",
            source_report_refs=(
                f"candidate-decision-team-memory:{candidate_id}:2026-07-07",
                f"candidate-resolution-risk:{market_id}:2026-07-07",
            ),
            adapter_reason_codes=(
                "team_memory_adapter_allow",
                "resolution_risk_adapter_passed",
            ),
        ),
        config=CandidateDecisionScoreConfig(config_version="candidate-decision-score-v1"),
        generated_at=generated_at,
    )


def _history_report() -> CandidateDecisionScoreHistoryReport:
    return build_candidate_decision_score_history_report(
        (
            _score_report(
                generated_at=datetime(2026, 7, 7, 11, 10, tzinfo=UTC),
                candidate_id="candidate-alpha",
                market_id="market-alpha",
            ),
            _score_report(
                generated_at=datetime(2026, 7, 7, 7, 0, tzinfo=timezone(timedelta(hours=-4))),
                candidate_id="candidate-beta",
                market_id="market-beta",
                gross_edge=d("0.012000"),
            ),
            _score_report(
                generated_at=datetime(2026, 7, 7, 11, 5, tzinfo=UTC),
                candidate_id="candidate-gamma",
                market_id="market-gamma",
                evidence_score=d("0.100000"),
            ),
        ),
        generated_at=datetime(2026, 7, 7, 9, 0, tzinfo=timezone(timedelta(hours=-4))),
    )


def _canonical_payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_json_clean(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("history DB row JSON must not contain floats")
    if isinstance(value, Decimal):
        pytest.fail("history DB row JSON must not contain raw Decimals")
    if isinstance(value, datetime):
        pytest.fail("history DB row JSON must not contain raw datetimes")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            _assert_json_clean(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_json_clean(item)


def _row_values(row: object) -> dict[str, object]:
    return dict(row.__dict__)


def _unchecked_row(row: object, **overrides: object) -> object:
    malformed = object.__new__(type(row))
    values = _row_values(row)
    values.update(overrides)
    for field_name, value in values.items():
        object.__setattr__(malformed, field_name, value)
    return malformed


def test_candidate_decision_score_history_db_row_round_trips_report() -> None:
    codec = api()
    report = _history_report()

    row = codec.to_db_row(report)

    assert type(row) is codec.CandidateDecisionScoreHistoryDbRow
    assert row.report_sha256 == _canonical_payload_sha256(row.payload_json)
    assert row.generated_at == HISTORY_GENERATED_AT
    assert row.status == "observed"
    assert row.source_report_count == d("3.000000")
    assert row.report_count == d("3.000000")
    assert row.first_source_generated_at == datetime(2026, 7, 7, 11, 0, tzinfo=UTC)
    assert row.latest_generated_at == datetime(2026, 7, 7, 11, 10, tzinfo=UTC)
    assert row.candidate_count == d("3.000000")
    assert row.action_reject_count == d("1.000000")
    assert row.action_watch_count == d("1.000000")
    assert row.action_research_more_count == d("0.000000")
    assert row.action_paper_recommend_count == d("1.000000")
    assert row.hard_blocked_count == d("1.000000")
    assert row.blocked_total == d("1.000000")
    assert row.watch_total == d("1.000000")
    assert row.paper_recommend_total == d("1.000000")
    assert row.action_counts_json == row.payload_json["action_counts"]
    assert row.hard_blocker_code_counts_json == row.payload_json["hard_blocker_code_counts"]
    assert row.reason_code_counts_json == row.payload_json["reason_code_counts"]
    assert row.reason_counts_json == row.payload_json["reason_counts"]
    assert row.primary_team_counts_json == row.payload_json["primary_team_counts"]
    assert row.public_summary_json["action_counts"] == row.action_counts_json
    assert row.public_summary_json["reason_counts"] == row.reason_counts_json
    assert "rows" not in row.public_summary_json
    public_blob = json.dumps(row.public_summary_json, sort_keys=True)
    for private_value in (
        "candidate-alpha",
        "candidate-beta",
        "candidate-gamma",
        "market-alpha",
        "market-beta",
        "market-gamma",
    ):
        assert private_value not in public_blob
    assert row.payload_json["generated_at"] == "2026-07-07T13:00:00+00:00"
    assert row.payload_json["source_report_count"] == "3.000000"
    assert row.payload_json["rows"][0]["source_generated_at"] == (
        "2026-07-07T11:00:00+00:00"
    )
    assert row.payload_json["rows"][0]["decision_score"] == "0.800000"
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    _assert_json_clean(row.action_counts_json)
    _assert_json_clean(row.hard_blocker_code_counts_json)
    _assert_json_clean(row.reason_code_counts_json)
    _assert_json_clean(row.reason_counts_json)
    _assert_json_clean(row.primary_team_counts_json)
    _assert_json_clean(row.public_summary_json)
    _assert_json_clean(row.payload_json)

    assert codec.from_db_row(row) == report
    assert codec.candidate_decision_score_history_report_to_db_row(report) == row
    assert codec.candidate_decision_score_history_report_from_db_row(row) == report


def test_candidate_decision_score_history_db_row_uses_decimal_strings_and_no_floats() -> None:
    codec = api()
    row = codec.to_db_row(_history_report())

    top_level_decimal_fields = (
        "source_report_count",
        "report_count",
        "candidate_count",
        "action_reject_count",
        "action_watch_count",
        "action_research_more_count",
        "action_paper_recommend_count",
        "hard_blocked_count",
        "blocked_total",
        "watch_total",
        "paper_recommend_total",
    )
    for field_name in top_level_decimal_fields:
        assert type(row.payload_json[field_name]) is str
        assert row.payload_json[field_name].endswith("0000")
        assert row.public_summary_json[field_name] == row.payload_json[field_name]
    for row_payload in row.payload_json["rows"]:
        assert type(row_payload["decision_score"]) is str
        assert type(row_payload["hard_blocker_count"]) is str
    for aggregate_name in (
        "action_counts",
        "hard_blocker_code_counts",
        "reason_code_counts",
        "reason_counts",
        "primary_team_counts",
    ):
        for aggregate_row in row.payload_json[aggregate_name]:
            assert type(aggregate_row["count"]) is str
            assert aggregate_row["count"].endswith("0000")

    _assert_json_clean(row.public_summary_json)
    _assert_json_clean(row.payload_json)


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_candidate_decision_score_history_db_row_enforces_hard_flags(flag_name: str) -> None:
    codec = api()
    report = _history_report()
    object.__setattr__(report, flag_name, False)

    with pytest.raises(ValueError, match=flag_name):
        codec.to_db_row(report)

    report = _history_report()
    row = codec.to_db_row(report)
    payload = deepcopy(row.payload_json)
    payload["rows"][0][flag_name] = False

    with pytest.raises(ValueError, match=flag_name):
        codec.CandidateDecisionScoreHistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_candidate_decision_score_history_db_row_rejects_unsafe_row_payloads() -> None:
    codec = api()
    row = codec.to_db_row(_history_report())

    public_summary = deepcopy(row.public_summary_json)
    public_summary["wallet_balance"] = "0.000000"
    with pytest.raises(ValueError, match="unsafe"):
        codec.CandidateDecisionScoreHistoryDbRow(
            **{
                **_row_values(row),
                "public_summary_json": public_summary,
            },
        )

    payload = deepcopy(row.payload_json)
    payload["rows"][0]["candidate_id"] = "wallet-candidate"
    with pytest.raises(ValueError, match="unsafe"):
        codec.CandidateDecisionScoreHistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_candidate_decision_score_history_db_row_rejects_tampered_payloads() -> None:
    codec = api()
    row = codec.to_db_row(_history_report())

    payload = deepcopy(row.payload_json)
    payload["source_report_count"] = "4.000000"
    public_summary = deepcopy(row.public_summary_json)
    public_summary["source_report_count"] = "4.000000"

    with pytest.raises(ValueError, match="source_report_count|payload_json"):
        codec.from_db_row(
            _unchecked_row(
                row,
                report_sha256=_canonical_payload_sha256(payload),
                source_report_count=d("4.000000"),
                public_summary_json=public_summary,
                payload_json=payload,
            ),
        )


@pytest.mark.parametrize(
    "field_name",
    ("generated_at", "first_source_generated_at", "latest_generated_at"),
)
def test_candidate_decision_score_history_db_row_requires_timezone_aware_materialized_datetimes(
    field_name: str,
) -> None:
    codec = api()
    row = codec.to_db_row(_history_report())

    with pytest.raises(ValueError, match="timezone-aware"):
        codec.CandidateDecisionScoreHistoryDbRow(
            **{
                **_row_values(row),
                field_name: datetime(2026, 7, 7, 12, 30),
            },
        )


def test_candidate_decision_score_history_db_row_requires_timezone_aware_payload_datetimes() -> None:
    codec = api()
    row = codec.to_db_row(_history_report())
    payload = deepcopy(row.payload_json)
    payload["rows"][0]["source_generated_at"] = "2026-07-07T11:00:00"

    with pytest.raises(ValueError, match="timezone-aware"):
        codec.CandidateDecisionScoreHistoryDbRow(
            **{
                **_row_values(row),
                "report_sha256": _canonical_payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_candidate_decision_score_history_db_row_is_frozen_and_has_no_public_storage_config() -> None:
    codec = api()
    row = codec.to_db_row(_history_report())

    with pytest.raises(FrozenInstanceError):
        row.status = "empty"  # type: ignore[misc]

    field_names = {field.name for field in fields(codec.CandidateDecisionScoreHistoryDbRow)}
    assert "table_name" not in field_names
    assert "dsn" not in field_names


def test_candidate_decision_score_history_db_row_module_keeps_pure_mapping_boundary() -> None:
    source_path = Path("src/polymarket_alpha_lab/candidate_decision_score_history_db_row.py")
    assert source_path.exists(), "missing candidate decision score history DB row module"
    source = source_path.read_text(encoding="utf-8").lower()
    import_lines = tuple(
        line.strip()
        for line in source.splitlines()
        if line.startswith("import ") or line.startswith("from ")
    )

    forbidden_imports = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "click",
        "argparse",
        "pathlib",
        "os",
        "sys",
    )
    assert [
        term
        for term in forbidden_imports
        if any(term in import_line for import_line in import_lines)
    ] == []

    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "socket",
        "subprocess",
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "click",
        "argparse",
        "environ",
        "getenv",
        "open(",
        ".write(",
        "private_key",
        "place_order",
        "create_order",
        "cancel_order",
        "replace_order",
        "live_trading",
    )
    assert [term for term in forbidden_terms if term in source] == []
