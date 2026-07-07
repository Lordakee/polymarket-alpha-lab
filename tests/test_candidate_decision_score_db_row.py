from __future__ import annotations

from copy import deepcopy
from dataclasses import FrozenInstanceError, replace
from datetime import UTC, datetime, timezone, timedelta
from decimal import Decimal
import hashlib
import json
from pathlib import Path

import pytest

from polymarket_alpha_lab.candidate_decision_score import (
    CandidateDecisionScoreConfig,
    CandidateDecisionScoreInput,
    CandidateDecisionScoreReport,
    build_candidate_decision_score_report,
)
from polymarket_alpha_lab.candidate_decision_score_db_row import (
    CandidateDecisionScoreDbRow,
    candidate_decision_score_report_from_db_row,
    candidate_decision_score_report_to_db_row,
)


GENERATED_AT = datetime(2026, 7, 7, 12, 30, tzinfo=UTC)


def d(value: str) -> Decimal:
    return Decimal(value)


def _report(
    *,
    generated_at: datetime = GENERATED_AT,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> CandidateDecisionScoreReport:
    report = build_candidate_decision_score_report(
        CandidateDecisionScoreInput(
            candidate_id="candidate-1",
            market_id="market-1",
            normalized_market_question="Will candidate 1 resolve yes?",
            primary_team_id="politics",
            secondary_team_ids=("crypto_btc",),
            selected_side="yes",
            forecast_probability=d("0.620000"),
            executable_price=d("0.560000"),
            gross_edge=d("0.060000"),
            estimated_cost_drag=d("0.010000"),
            cost_score=d("0.800000"),
            liquidity_score=d("0.900000"),
            evidence_score=d("0.850000"),
            resolution_score=d("0.700000"),
            team_memory_score=d("0.750000"),
            team_memory_policy="allow",
            source_report_refs=(
                "candidate-decision-team-memory:politics:2026-07-07",
                "candidate-resolution-risk:market-1:2026-07-07",
            ),
            adapter_reason_codes=(
                "team_memory_adapter_allow",
                "resolution_risk_adapter_passed",
            ),
        ),
        config=CandidateDecisionScoreConfig(config_version="candidate-decision-score-v1"),
        generated_at=generated_at,
    )
    object.__setattr__(report, "paper_only", paper_only)
    object.__setattr__(report, "report_only", report_only)
    object.__setattr__(report, "readonly", readonly)
    return report


def _payload_sha256(payload_json: dict[str, object]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_json_clean(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload_json must not contain floats")
    if isinstance(value, Decimal):
        pytest.fail("payload_json must not contain raw Decimal values")
    if isinstance(value, datetime):
        pytest.fail("payload_json must not contain raw datetime values")
    if isinstance(value, dict):
        for key, item in value.items():
            assert type(key) is str
            _assert_json_clean(item)
    elif isinstance(value, (list, tuple)):
        for item in value:
            _assert_json_clean(item)


def _row_values(row: CandidateDecisionScoreDbRow) -> dict[str, object]:
    return {
        "report_sha256": row.report_sha256,
        "generated_at": row.generated_at,
        "config_version": row.config_version,
        "candidate_id": row.candidate_id,
        "market_id": row.market_id,
        "primary_team_id": row.primary_team_id,
        "action": row.action,
        "decision_score": row.decision_score,
        "reason_codes_json": row.reason_codes_json,
        "source_report_refs_json": row.source_report_refs_json,
        "payload_json": row.payload_json,
        "paper_only": row.paper_only,
        "report_only": row.report_only,
        "readonly": row.readonly,
    }


def _unchecked_row(
    row: CandidateDecisionScoreDbRow,
    **overrides: object,
) -> CandidateDecisionScoreDbRow:
    malformed = object.__new__(CandidateDecisionScoreDbRow)
    values = _row_values(row)
    values.update(overrides)
    for field_name, value in values.items():
        object.__setattr__(malformed, field_name, value)
    return malformed


def test_candidate_decision_score_db_row_round_trips_report() -> None:
    report = _report(
        generated_at=datetime(2026, 7, 7, 8, 30, tzinfo=timezone(timedelta(hours=-4))),
    )

    row = candidate_decision_score_report_to_db_row(report)

    assert type(row) is CandidateDecisionScoreDbRow
    assert row.report_sha256 == _payload_sha256(row.payload_json)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "candidate-decision-score-v1"
    assert row.candidate_id == "candidate-1"
    assert row.market_id == "market-1"
    assert row.primary_team_id == "politics"
    assert row.action == "paper_recommend"
    assert row.decision_score == d("0.800000")
    assert row.reason_codes_json == [
        "candidate_decision_paper_recommend",
        "resolution_risk_adapter_passed",
        "team_memory_adapter_allow",
    ]
    assert row.source_report_refs_json == [
        "candidate-decision-team-memory:politics:2026-07-07",
        "candidate-resolution-risk:market-1:2026-07-07",
    ]
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert row.payload_json["generated_at"] == "2026-07-07T12:30:00+00:00"
    assert row.payload_json["decision_score"] == "0.800000"
    assert row.payload_json["net_edge"] == "0.050000"
    assert row.payload_json["reason_codes"] == row.reason_codes_json
    assert row.payload_json["source_report_refs"] == row.source_report_refs_json
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    _assert_json_clean(row.payload_json)

    assert candidate_decision_score_report_from_db_row(row) == report


def test_candidate_decision_score_db_row_hash_is_deterministic_for_canonical_payloads() -> None:
    first = candidate_decision_score_report_to_db_row(_report())
    second = candidate_decision_score_report_to_db_row(
        _report(
            generated_at=datetime(
                2026,
                7,
                7,
                8,
                30,
                tzinfo=timezone(timedelta(hours=-4)),
            ),
        ),
    )
    different = candidate_decision_score_report_to_db_row(
        _report(generated_at=datetime(2026, 7, 7, 12, 31, tzinfo=UTC)),
    )

    assert first.payload_json == second.payload_json
    assert first.report_sha256 == second.report_sha256
    assert first.report_sha256 != different.report_sha256


def test_candidate_decision_score_db_row_payload_uses_decimal_strings_and_no_floats() -> None:
    row = candidate_decision_score_report_to_db_row(_report())

    for field_name in (
        "forecast_probability",
        "executable_price",
        "gross_edge",
        "estimated_cost_drag",
        "net_edge",
        "cost_score",
        "liquidity_score",
        "evidence_score",
        "resolution_score",
        "team_memory_score",
        "decision_score",
    ):
        assert type(row.payload_json[field_name]) is str
        assert row.payload_json[field_name].endswith("0000")
    _assert_json_clean(row.payload_json)


@pytest.mark.parametrize(
    ("field_name", "bad_value"),
    (
        ("report_sha256", "a" * 64),
        ("generated_at", datetime(2026, 7, 7, 12, 31, tzinfo=UTC)),
        ("config_version", "candidate-decision-score-v2"),
        ("candidate_id", "candidate-2"),
        ("market_id", "market-2"),
        ("primary_team_id", "crypto_btc"),
        ("action", "watch"),
        ("decision_score", d("0.790000")),
        ("reason_codes_json", ["candidate_decision_watch"]),
        ("source_report_refs_json", ["candidate-resolution-risk:market-2:2026-07-07"]),
        ("paper_only", False),
        ("report_only", False),
        ("readonly", False),
    ),
)
def test_candidate_decision_score_db_row_rejects_materialized_mismatches(
    field_name: str,
    bad_value: object,
) -> None:
    row = candidate_decision_score_report_to_db_row(_report())

    with pytest.raises(ValueError, match=field_name):
        replace(row, **{field_name: bad_value})

    with pytest.raises(ValueError, match=field_name):
        candidate_decision_score_report_from_db_row(
            _unchecked_row(row, **{field_name: bad_value}),
        )


def test_candidate_decision_score_db_row_rejects_hash_mismatch() -> None:
    row = candidate_decision_score_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["candidate_id"] = "candidate-2"

    with pytest.raises(ValueError, match="report_sha256"):
        candidate_decision_score_report_from_db_row(
            _unchecked_row(row, payload_json=payload),
        )


def test_candidate_decision_score_db_row_rejects_self_hashed_tampered_payload() -> None:
    row = candidate_decision_score_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["decision_score"] = "0.810000"

    with pytest.raises(ValueError, match="payload_json|decision_score|derived_validation_digest"):
        candidate_decision_score_report_from_db_row(
            _unchecked_row(
                row,
                report_sha256=_payload_sha256(payload),
                decision_score=d("0.810000"),
                payload_json=payload,
            ),
        )


def test_candidate_decision_score_db_row_rejects_tampered_reason_codes() -> None:
    row = candidate_decision_score_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["reason_codes"] = ["candidate_decision_watch"]

    with pytest.raises(ValueError, match="reason_codes|payload_json|derived_validation_digest"):
        candidate_decision_score_report_from_db_row(
            _unchecked_row(
                row,
                report_sha256=_payload_sha256(payload),
                action="watch",
                reason_codes_json=["candidate_decision_watch"],
                payload_json=payload,
            ),
        )


@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_candidate_decision_score_db_row_enforces_hard_flags(flag_name: str) -> None:
    with pytest.raises(ValueError, match=flag_name):
        candidate_decision_score_report_to_db_row(_report(**{flag_name: False}))

    row = candidate_decision_score_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload[flag_name] = False

    with pytest.raises(ValueError, match=flag_name):
        CandidateDecisionScoreDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_candidate_decision_score_db_row_rejects_unsafe_payload_keys() -> None:
    row = candidate_decision_score_report_to_db_row(_report())
    payload = deepcopy(row.payload_json)
    payload["wallet_balance"] = "0.000000"

    with pytest.raises(ValueError, match="unsafe live surface field|wallet_balance"):
        CandidateDecisionScoreDbRow(
            **{
                **_row_values(row),
                "report_sha256": _payload_sha256(payload),
                "payload_json": payload,
            },
        )


def test_candidate_decision_score_db_row_rejects_raw_payload_values() -> None:
    row = candidate_decision_score_report_to_db_row(_report())

    for bad_value, match in (
        (0.8, "float"),
        (d("0.800000"), "Decimal"),
        (GENERATED_AT, "datetime"),
    ):
        payload = deepcopy(row.payload_json)
        payload["decision_score"] = bad_value
        with pytest.raises(ValueError, match=match):
            CandidateDecisionScoreDbRow(
                **{
                    **_row_values(row),
                    "payload_json": payload,
                },
            )


def test_candidate_decision_score_db_row_is_frozen() -> None:
    row = candidate_decision_score_report_to_db_row(_report())

    with pytest.raises(FrozenInstanceError):
        row.action = "watch"  # type: ignore[misc]


def test_candidate_decision_score_db_row_module_keeps_phase_two_boundary() -> None:
    source = Path(
        "src/polymarket_alpha_lab/candidate_decision_score_db_row.py",
    ).read_text(encoding="utf-8")

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
        "open(",
        ".write(",
        "wallet",
        "private_key",
        "account",
        "auth",
        "place_order",
        "create_order",
        "cancel_order",
        "exchange",
        "live_trading",
    )
    lowered = source.lower()

    assert [term for term in forbidden_terms if term in lowered] == []
