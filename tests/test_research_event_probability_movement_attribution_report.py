from __future__ import annotations

import hashlib
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest


api = importlib.import_module(
    "polymarket_alpha_lab.research_event_probability_movement_attribution_report",
)

GENERATED_AT = datetime(2026, 2, 4, 9, 15, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    values: dict[str, object] = {
        "config_version": (
            api.DEFAULT_RESEARCH_EVENT_PROBABILITY_MOVEMENT_ATTRIBUTION_REPORT_CONFIG_VERSION
        ),
        "material_probability_move_threshold": d("0.020000"),
        "attribution_score_threshold": d("0.550000"),
        "attribution_dominance_threshold": d("0.150000"),
        "fresh_evidence_max_age_hours": d("4.000000"),
        "book_movement_min_magnitude": d("0.050000"),
    }
    values.update(overrides)
    return api.ResearchEventProbabilityMovementAttributionConfig(**values)


def observation(
    *,
    observed_at: datetime = GENERATED_AT,
    probability_before: object = d("0.400000"),
    probability_after: object = d("0.520000"),
    fresh_evidence_score: object = d("0.800000"),
    book_movement_score: object = d("0.250000"),
    unresolved_noise_score: object = d("0.100000"),
    latest_fresh_evidence_age_hours: object = d("1.000000"),
    book_midpoint_move: object = d("0.020000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    return api.ResearchEventProbabilityMovementAttributionObservation(
        observed_at=observed_at,
        probability_before=probability_before,
        probability_after=probability_after,
        fresh_evidence_score=fresh_evidence_score,
        book_movement_score=book_movement_score,
        unresolved_noise_score=unresolved_noise_score,
        latest_fresh_evidence_age_hours=latest_fresh_evidence_age_hours,
        book_midpoint_move=book_midpoint_move,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(*rows: object, generated_at: datetime = GENERATED_AT, **config_overrides: object):
    return api.build_research_event_probability_movement_attribution_report(
        rows,
        config=config(**config_overrides),
        generated_at=generated_at,
    )


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    core = {
        key: item
        for key, item in payload.items()
        if key != "derived_validation_digest"
    }
    payload["derived_validation_digest"] = hashlib.sha256(
        json.dumps(core, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    return payload


def test_builds_deterministic_aggregate_attribution_report() -> None:
    fresh = observation()
    book = observation(
        probability_before=d("0.600000"),
        probability_after=d("0.500000"),
        fresh_evidence_score=d("0.200000"),
        book_movement_score=d("0.780000"),
        unresolved_noise_score=d("0.150000"),
        latest_fresh_evidence_age_hours=d("8.000000"),
        book_midpoint_move=d("0.110000"),
    )
    noise = observation(
        probability_before=d("0.300000"),
        probability_after=d("0.340000"),
        fresh_evidence_score=d("0.420000"),
        book_movement_score=d("0.400000"),
        unresolved_noise_score=d("0.600000"),
        latest_fresh_evidence_age_hours=d("12.000000"),
        book_midpoint_move=d("0.020000"),
    )

    built = report(noise, fresh, book)
    replayed = report(book, noise, fresh)

    assert built.payload == replayed.payload
    assert built.derived_validation_digest == replayed.derived_validation_digest
    assert built.report_status == "watch"
    assert built.observation_count == d("3.000000")
    assert built.fresh_evidence_count == d("1.000000")
    assert built.book_movement_count == d("1.000000")
    assert built.unresolved_noise_count == d("1.000000")
    assert built.pass_count == d("2.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("0.000000")
    assert built.total_movement_magnitude == d("0.260000")
    assert built.average_movement_magnitude == d("0.086667")
    assert tuple(row.rank for row in built.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )

    rows_by_category = {row.attribution_category: row for row in built.rows}
    fresh_row = rows_by_category["fresh_evidence"]
    assert fresh_row.movement_direction == "up"
    assert fresh_row.movement_magnitude == d("0.120000")
    assert fresh_row.attribution_status == "pass"
    assert fresh_row.reason_codes == (
        "movement_material",
        "fresh_evidence_dominant",
        "attribution_resolved",
    )

    book_row = rows_by_category["book_movement"]
    assert book_row.movement_direction == "down"
    assert book_row.attribution_status == "pass"
    assert "book_movement_dominant" in book_row.reason_codes
    assert "book_movement_material" in book_row.reason_codes

    noise_row = rows_by_category["unresolved_noise"]
    assert noise_row.movement_direction == "up"
    assert noise_row.attribution_status == "watch"
    assert noise_row.reason_codes == (
        "movement_material",
        "unresolved_noise_dominant",
        "attribution_unresolved",
    )

    payload = built.payload
    assert payload == api.research_event_probability_movement_attribution_report_payload(built)
    assert payload["generated_at"] == "2026-02-04T09:15:00Z"
    assert payload["observation_count"] == "3.000000"
    assert payload["rows"][0]["rank"] == "1.000000"
    assert_no_raw_private_identifiers(payload)
    assert_no_float_or_int_values(payload)
    json.dumps(payload, sort_keys=True)
    assert (
        api.derive_research_event_probability_movement_attribution_report_digest(payload)
        == built.derived_validation_digest
    )


def test_below_material_probability_movement_blocks_attribution() -> None:
    built = report(
        observation(
            probability_before=d("0.500000"),
            probability_after=d("0.505000"),
            fresh_evidence_score=d("0.900000"),
        ),
    )

    assert built.report_status == "block"
    assert built.block_count == d("1.000000")
    assert built.unresolved_noise_count == d("1.000000")
    row = built.rows[0]
    assert row.attribution_category == "unresolved_noise"
    assert row.attribution_status == "block"
    assert row.reason_codes == (
        "movement_below_materiality",
        "attribution_blocked",
    )


def test_digest_and_payload_validation_reject_tampering() -> None:
    built = report(observation())

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, derived_validation_digest="0" * 64)

    count_drift = built.payload
    count_drift["fresh_evidence_count"] = "99.000000"
    resign_payload(count_drift)
    with pytest.raises(ValueError, match="fresh_evidence_count"):
        api.research_event_probability_movement_attribution_report_payload(count_drift)

    row_drift = built.payload
    row_drift["rows"][0]["movement_magnitude"] = "0.990000"
    resign_payload(row_drift)
    with pytest.raises(ValueError, match="movement_magnitude"):
        api.research_event_probability_movement_attribution_report_payload(row_drift)

    forbidden = built.payload
    forbidden["market_id"] = "raw-identifier"
    resign_payload(forbidden)
    with pytest.raises(ValueError, match="unsafe|supported"):
        api.research_event_probability_movement_attribution_report_payload(forbidden)


def test_frozen_decimal_only_inputs_and_hard_flags_are_enforced() -> None:
    built = report(observation())

    for value in (config(), observation(), built.rows[0], built):
        assert is_dataclass(value)
        with pytest.raises(FrozenInstanceError):
            value.readonly = False  # type: ignore[misc]

    with pytest.raises(ValueError, match="probability_before"):
        observation(probability_before=_DecimalSubclass("0.400000"))
    with pytest.raises(ValueError, match="probability_after"):
        observation(probability_after=0.52)
    with pytest.raises(ValueError, match="fresh_evidence_score"):
        observation(fresh_evidence_score=1)
    with pytest.raises(ValueError, match="latest_fresh_evidence_age_hours"):
        observation(latest_fresh_evidence_age_hours=d("-1.000000"))
    with pytest.raises(ValueError, match="book_midpoint_move"):
        observation(book_midpoint_move=d("-0.010000"))
    with pytest.raises(ValueError, match="paper_only"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="readonly"):
        replace(built.rows[0], readonly=False)
    with pytest.raises(ValueError, match="threshold"):
        config(attribution_dominance_threshold=d("0.600000"))


def test_static_public_surface_is_report_only_and_identifier_free() -> None:
    module_source = Path(api.__file__).read_text(encoding="utf-8").lower()
    forbidden_source_fragments = (
        "requests",
        "httpx",
        "urllib",
        "socket",
        "sqlite3",
        "psycopg",
        "sqlalchemy",
        "web3",
        "ccxt",
        "subprocess",
        "open(",
        "candidate_id",
        "market_id",
        "market_slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table_name",
        "private_token",
        "wallet",
        "auth",
        "order",
        "sizing",
        "recommendation",
    )
    for forbidden in forbidden_source_fragments:
        assert forbidden not in module_source

    assert api.__all__ == (
        "DEFAULT_RESEARCH_EVENT_PROBABILITY_MOVEMENT_ATTRIBUTION_REPORT_CONFIG_VERSION",
        "ResearchEventProbabilityMovementAttributionConfig",
        "ResearchEventProbabilityMovementAttributionObservation",
        "ResearchEventProbabilityMovementAttributionReport",
        "ResearchEventProbabilityMovementAttributionRow",
        "build_research_event_probability_movement_attribution_report",
        "derive_research_event_probability_movement_attribution_report_digest",
        "research_event_probability_movement_attribution_report_payload",
    )

    unsafe_field_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    )
    for cls in (
        api.ResearchEventProbabilityMovementAttributionConfig,
        api.ResearchEventProbabilityMovementAttributionObservation,
        api.ResearchEventProbabilityMovementAttributionRow,
        api.ResearchEventProbabilityMovementAttributionReport,
    ):
        for field in fields(cls):
            lowered = field.name.lower()
            assert not any(fragment in lowered for fragment in unsafe_field_fragments)


def assert_no_float_or_int_values(value: Any) -> None:
    if type(value) is int or isinstance(value, float):
        raise AssertionError(f"numeric payload value is not a Decimal string: {value!r}")
    if isinstance(value, dict):
        for item in value.values():
            assert_no_float_or_int_values(item)
    if isinstance(value, list):
        for item in value:
            assert_no_float_or_int_values(item)


def assert_no_raw_private_identifiers(value: Any) -> None:
    forbidden_fragments = (
        "candidate",
        "market",
        "slug",
        "question",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            lowered = key.lower()
            assert not any(fragment in lowered for fragment in forbidden_fragments)
            assert_no_raw_private_identifiers(item)
    if isinstance(value, list):
        for item in value:
            assert_no_raw_private_identifiers(item)
