from __future__ import annotations

from dataclasses import fields
from datetime import UTC, datetime
from decimal import Decimal
import hashlib
import json
import re
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.team_forecast_db_row import (
    TeamForecastDbRow,
    TeamForecastEvidenceDbRow,
    TeamForecastOutcome,
    TeamForecastOutcomeDbRow,
    TeamMarketRouteDbRow,
    team_forecast_evidence_from_db_row,
    team_forecast_evidence_to_db_row,
    team_forecast_from_db_row,
    team_forecast_outcome_from_db_row,
    team_forecast_outcome_to_db_row,
    team_forecast_to_db_row,
    team_route_from_db_row,
    team_route_to_db_row,
)
from polymarket_alpha_lab.team_forecast_packet import (
    TeamForecastEvidencePacket,
    TeamForecastPacket,
)
from polymarket_alpha_lab.team_market_router import (
    TeamMarketRouteConfig,
    TeamMarketRouteInput,
    build_team_market_route_report,
)


GENERATED_AT = datetime(2026, 7, 1, 12, 0, tzinfo=UTC)
DATA_TIMESTAMP = datetime(2026, 7, 1, 11, 58, tzinfo=UTC)
SHA256_RE = re.compile(r"^[a-f0-9]{64}$")


def d(value: str) -> Decimal:
    return Decimal(value)


def _payload_sha256(payload_json: dict[str, Any]) -> str:
    encoded = json.dumps(
        payload_json,
        allow_nan=False,
        separators=(",", ":"),
        sort_keys=True,
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _assert_no_floats(value: object) -> None:
    if isinstance(value, float):
        pytest.fail("payload_json must not contain floats")
    if isinstance(value, dict):
        for item in value.values():
            _assert_no_floats(item)
    elif isinstance(value, list):
        for item in value:
            _assert_no_floats(item)


def _row_values(row: object) -> dict[str, Any]:
    return {field.name: getattr(row, field.name) for field in fields(row)}


def _payload_copy(row: object) -> dict[str, Any]:
    return json.loads(json.dumps(getattr(row, "payload_json"), allow_nan=False))


def _set_payload_path(
    payload_json: dict[str, Any],
    path: tuple[str | int, ...],
    value: Any,
) -> None:
    target: Any = payload_json
    for key in path[:-1]:
        target = target[key]
    target[path[-1]] = value


def _row_with_payload(row: object, payload_json: dict[str, Any], **overrides: Any):
    kwargs = _row_values(row)
    kwargs.update(
        payload_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )
    kwargs.update(overrides)
    return type(row)(**kwargs)


def _bypassed_row(row: object, **overrides: Any):
    malformed = object.__new__(type(row))
    kwargs = _row_values(row)
    kwargs.update(overrides)
    for key, value in kwargs.items():
        object.__setattr__(malformed, key, value)
    return malformed


def _route_report():
    return build_team_market_route_report(
        (
            TeamMarketRouteInput(
                condition_id="condition-btc",
                market_slug="bitcoin-above-120k",
                question="Will Bitcoin hit 120000 before August 31?",
                category_hint="finance.crypto.btc",
                event_template="btc_hit_price",
                routing_reason_codes=("keyword_bitcoin", "template_hit_price"),
            ),
        ),
        config=TeamMarketRouteConfig(config_version="team-router-v0"),
        generated_at=GENERATED_AT,
    )


def _forecast_packet() -> TeamForecastPacket:
    return TeamForecastPacket(
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        condition_id="condition-btc",
        market_slug="bitcoin-above-120k",
        question="Will Bitcoin hit 120000 before August 31?",
        category_id="finance.crypto.btc",
        event_template="btc_hit_price",
        selected_side="yes",
        forecast_probability=d("0.620000"),
        confidence=d("0.710000"),
        evidence_quality=d("0.800000"),
        data_freshness_score=d("0.900000"),
        resolution_risk=d("0.100000"),
        base_rate=d("0.540000"),
        market_implied_probability_observed=d("0.570000"),
        reason_codes=("team_crypto_btc", "flow_support"),
        memory_references=("btc-memory-2026-q2",),
        source_references=("source-etf-flow-dashboard",),
        known_failure_modes=("weekend_liquidity_gap",),
        config_version="team-forecast-v0",
        prompt_version="btc-team-prompt-v0",
        generated_at=GENERATED_AT,
    )


def _evidence_packet() -> TeamForecastEvidencePacket:
    return TeamForecastEvidencePacket(
        evidence_id="evidence-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        source_id="source-etf-flow-dashboard",
        source_type="market_data",
        data_timestamp=DATA_TIMESTAMP,
        data_freshness_seconds=120,
        evidence_type="etf_flow",
        evidence_text="US spot ETF net flow improved over the last session.",
        weight=d("0.420000"),
        reason_codes=("team_crypto_btc", "flow_support"),
    )


def _outcome() -> TeamForecastOutcome:
    return TeamForecastOutcome(
        outcome_id="outcome-btc-1",
        forecast_id="forecast-btc-1",
        team_id="crypto_btc",
        market_slug="bitcoin-above-120k",
        actual_outcome="yes",
        resolved_at=GENERATED_AT,
        settlement_source="polymarket_public_resolution",
        forecast_error=d("0.380000"),
        brier_score=d("0.144400"),
        paper_pnl=d("0.000000"),
        cost_adjusted_return=d("0.000000"),
        directionally_correct=True,
        profitable_after_cost=False,
        resolution_dispute_flag=False,
        reason_codes=("settled_yes",),
    )


def _route_row() -> TeamMarketRouteDbRow:
    return team_route_to_db_row(_route_report())


def _forecast_row() -> TeamForecastDbRow:
    return team_forecast_to_db_row(_forecast_packet())


def _evidence_row() -> TeamForecastEvidenceDbRow:
    return team_forecast_evidence_to_db_row(
        _evidence_packet(),
        forecast_id="forecast-btc-1",
        config_version="team-forecast-evidence-v0",
        generated_at=GENERATED_AT,
    )


def _outcome_row() -> TeamForecastOutcomeDbRow:
    return team_forecast_outcome_to_db_row(
        _outcome(),
        config_version="team-forecast-outcome-v0",
        generated_at=GENERATED_AT,
    )


def _assert_payload_sha256(row: object) -> None:
    payload_sha256 = getattr(row, "payload_sha256")
    assert SHA256_RE.fullmatch(payload_sha256)
    assert payload_sha256 == _payload_sha256(getattr(row, "payload_json"))


def test_team_forecast_db_row_module_is_pure_readonly_codec() -> None:
    source = Path("src/polymarket_alpha_lab/team_forecast_db_row.py").read_text(
        encoding="utf-8",
    )

    for banned in (
        "psycopg",
        "sqlite",
        "sqlalchemy",
        "private_key",
        "wallet",
        "api_key",
        "submit_order",
        "cancel_order",
        "replace_order",
        "live_trading",
    ):
        assert banned not in source.lower()


def test_route_db_row_uses_canonical_payload_and_round_trips() -> None:
    report = _route_report()
    row = team_route_to_db_row(report)

    assert type(row) is TeamMarketRouteDbRow
    _assert_payload_sha256(row)
    _assert_no_floats(row.payload_json)
    assert row.generated_at == GENERATED_AT
    assert row.team_id == "crypto_btc"
    assert row.market_slug == "bitcoin-above-120k"
    assert row.config_version == "team-router-v0"
    assert row.condition_id == "condition-btc"
    assert row.category_id == "finance.crypto.btc"
    assert row.event_template == "btc_hit_price"
    assert row.routing_confidence == d("0.900000")
    assert row.payload_json["generated_at"] == "2026-07-01T12:00:00+00:00"
    assert row.payload_json["rows"][0]["primary_team_id"] == row.team_id
    assert row.payload_json["rows"][0]["market_slug"] == row.market_slug
    assert row.payload_json["rows"][0]["routing_confidence"] == "0.900000"
    assert row.paper_only is True
    assert row.report_only is True
    assert row.readonly is True
    assert team_route_from_db_row(row) == report


def test_forecast_db_row_uses_canonical_payload_and_round_trips() -> None:
    packet = _forecast_packet()
    row = team_forecast_to_db_row(packet)

    assert type(row) is TeamForecastDbRow
    _assert_payload_sha256(row)
    _assert_no_floats(row.payload_json)
    assert row.generated_at == GENERATED_AT
    assert row.forecast_id == "forecast-btc-1"
    assert row.condition_id == "condition-btc"
    assert row.team_id == "crypto_btc"
    assert row.market_slug == "bitcoin-above-120k"
    assert row.config_version == "team-forecast-v0"
    assert row.selected_side == "yes"
    assert row.forecast_probability == d("0.620000")
    assert row.confidence == d("0.710000")
    assert row.payload_json["forecast_probability"] == "0.620000"
    assert row.payload_json["confidence"] == "0.710000"
    assert row.payload_json["team_id"] == row.team_id
    assert row.payload_json["market_slug"] == row.market_slug
    assert row.payload_json["paper_only"] is True
    assert row.payload_json["report_only"] is True
    assert row.payload_json["readonly"] is True
    assert team_forecast_from_db_row(row) == packet


def test_evidence_db_row_uses_canonical_payload_and_round_trips() -> None:
    packet = _evidence_packet()
    row = team_forecast_evidence_to_db_row(
        packet,
        forecast_id="forecast-btc-1",
        config_version="team-forecast-evidence-v0",
        generated_at=GENERATED_AT,
    )

    assert type(row) is TeamForecastEvidenceDbRow
    _assert_payload_sha256(row)
    _assert_no_floats(row.payload_json)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "team-forecast-evidence-v0"
    assert row.forecast_id == "forecast-btc-1"
    assert row.evidence_id == "evidence-btc-1"
    assert row.team_id == "crypto_btc"
    assert row.market_slug == "bitcoin-above-120k"
    assert row.source_id == "source-etf-flow-dashboard"
    assert row.data_timestamp == DATA_TIMESTAMP
    assert row.data_freshness_seconds == 120
    assert row.evidence_type == "etf_flow"
    assert row.weight == d("0.420000")
    assert row.payload_json["forecast_id"] == row.forecast_id
    assert row.payload_json["evidence"]["weight"] == "0.420000"
    assert row.payload_json["evidence"]["data_timestamp"] == (
        "2026-07-01T11:58:00+00:00"
    )
    assert team_forecast_evidence_from_db_row(row) == packet


def test_outcome_db_row_contains_plan_fields_and_round_trips() -> None:
    outcome = _outcome()
    row = team_forecast_outcome_to_db_row(
        outcome,
        config_version="team-forecast-outcome-v0",
        generated_at=GENERATED_AT,
    )

    assert type(row) is TeamForecastOutcomeDbRow
    _assert_payload_sha256(row)
    _assert_no_floats(row.payload_json)
    assert row.generated_at == GENERATED_AT
    assert row.config_version == "team-forecast-outcome-v0"
    assert row.outcome_id == "outcome-btc-1"
    assert row.forecast_id == "forecast-btc-1"
    assert row.team_id == "crypto_btc"
    assert row.market_slug == "bitcoin-above-120k"
    assert row.resolved_at == GENERATED_AT
    assert row.actual_outcome == "yes"
    assert row.forecast_error == d("0.380000")
    assert row.brier_score == d("0.144400")
    assert row.paper_pnl == d("0.000000")
    assert row.cost_adjusted_return == d("0.000000")
    assert row.directionally_correct is True
    assert row.profitable_after_cost is False
    assert row.resolution_dispute_flag is False
    assert row.payload_json["outcome"]["forecast_error"] == "0.380000"
    assert row.payload_json["outcome"]["brier_score"] == "0.144400"
    assert row.payload_json["outcome"]["paper_pnl"] == "0.000000"
    assert row.payload_json["outcome"]["cost_adjusted_return"] == "0.000000"
    assert row.payload_json["outcome"]["directionally_correct"] is True
    assert row.payload_json["outcome"]["profitable_after_cost"] is False
    assert row.payload_json["outcome"]["resolution_dispute_flag"] is False
    assert team_forecast_outcome_from_db_row(row) == outcome


@pytest.mark.parametrize(
    "row_factory",
    (_route_row, _forecast_row, _evidence_row, _outcome_row),
)
@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_db_rows_reject_false_safety_flags(row_factory, flag_name: str) -> None:
    row = row_factory()
    payload_json = _payload_copy(row)
    payload_json[flag_name] = False

    with pytest.raises(ValueError, match=flag_name):
        _row_with_payload(row, payload_json, **{flag_name: False})


@pytest.mark.parametrize(
    "row_factory",
    (_route_row, _forecast_row, _evidence_row, _outcome_row),
)
@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_db_rows_reject_missing_top_level_safety_flags(
    row_factory,
    flag_name: str,
) -> None:
    row = row_factory()
    payload_json = _payload_copy(row)
    del payload_json[flag_name]

    with pytest.raises(ValueError, match=flag_name):
        _row_with_payload(row, payload_json)


@pytest.mark.parametrize(
    ("row_factory", "nested_key"),
    ((_evidence_row, "evidence"), (_outcome_row, "outcome")),
)
@pytest.mark.parametrize("flag_name", ("paper_only", "report_only", "readonly"))
def test_nested_payloads_reject_missing_safety_flags(
    row_factory,
    nested_key: str,
    flag_name: str,
) -> None:
    row = row_factory()
    payload_json = _payload_copy(row)
    del payload_json[nested_key][flag_name]

    with pytest.raises(ValueError, match=flag_name):
        _row_with_payload(row, payload_json)


@pytest.mark.parametrize(
    "row_factory",
    (_route_row, _forecast_row, _evidence_row, _outcome_row),
)
def test_db_rows_reject_unsafe_payload_fields(row_factory) -> None:
    row = row_factory()
    payload_json = _payload_copy(row)
    payload_json["order_submission"] = "never"

    with pytest.raises(ValueError, match="unsafe live surface field"):
        _row_with_payload(row, payload_json)


def test_db_rows_reject_payload_floats_and_materialized_mismatches() -> None:
    row = _forecast_row()
    payload_json = _payload_copy(row)
    payload_json["forecast_probability"] = 0.62

    with pytest.raises(ValueError, match="float"):
        _row_with_payload(row, payload_json)

    mismatched_payload = _payload_copy(row)
    mismatched_payload["market_slug"] = "bitcoin-above-130k"

    with pytest.raises(ValueError, match="market_slug must match payload_json"):
        _row_with_payload(row, mismatched_payload)


@pytest.mark.parametrize(
    ("row_factory", "from_db_row", "payload_path", "noncanonical_value"),
    (
        (
            _route_row,
            team_route_from_db_row,
            ("rows", 0, "routing_confidence"),
            "0.9000004",
        ),
        (
            _forecast_row,
            team_forecast_from_db_row,
            ("forecast_probability",),
            "0.6200004",
        ),
        (
            _evidence_row,
            team_forecast_evidence_from_db_row,
            ("evidence", "weight"),
            "0.4200004",
        ),
        (
            _outcome_row,
            team_forecast_outcome_from_db_row,
            ("outcome", "forecast_error"),
            "0.3800004",
        ),
    ),
)
def test_db_rows_reject_noncanonical_decimal_payload_strings_even_when_hash_matches(
    row_factory,
    from_db_row,
    payload_path: tuple[str | int, ...],
    noncanonical_value: str,
) -> None:
    row = row_factory()
    payload_json = _payload_copy(row)
    _set_payload_path(payload_json, payload_path, noncanonical_value)

    with pytest.raises(ValueError, match="canonical"):
        _row_with_payload(row, payload_json)

    bypassed_row = _bypassed_row(
        row,
        payload_sha256=_payload_sha256(payload_json),
        payload_json=payload_json,
    )
    with pytest.raises(ValueError, match="canonical"):
        from_db_row(bypassed_row)


def test_from_db_row_rejects_constructor_bypassed_malformed_row() -> None:
    row = _forecast_row()
    malformed = _bypassed_row(row, market_slug="bitcoin-above-130k")

    with pytest.raises(ValueError, match="market_slug must match payload_json"):
        team_forecast_from_db_row(malformed)

    corrupted_payload = _payload_copy(row)
    corrupted_payload["readonly"] = False
    corrupted_payload_row = _bypassed_row(
        row,
        payload_sha256=_payload_sha256(corrupted_payload),
        payload_json=corrupted_payload,
    )

    with pytest.raises(ValueError, match="readonly"):
        team_forecast_from_db_row(corrupted_payload_row)
