from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_source_real_time_event_update_pressure_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_source_real_time_event_update_pressure_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def config(**overrides: object) -> Any:
    module = api()
    values: dict[str, object] = {
        "config_version": "real-time-event-update-pressure-test-v0",
        "max_pass_update_age_seconds": d("900.000000"),
        "max_watch_update_age_seconds": d("3600.000000"),
        "watch_update_velocity_per_hour": d("4.000000"),
        "block_update_velocity_per_hour": d("8.000000"),
        "min_pass_corroboration_score": d("0.750000"),
        "min_watch_corroboration_score": d("0.500000"),
        "max_pass_contradiction_pressure": d("0.100000"),
        "max_watch_contradiction_pressure": d("0.400000"),
        "min_pass_extraction_confidence_score": d("0.800000"),
        "min_watch_extraction_confidence_score": d("0.600000"),
        "max_pass_pressure_score": d("0.350000"),
        "max_watch_pressure_score": d("0.700000"),
        "update_velocity_weight": d("0.250000"),
        "authority_tier_weight": d("0.150000"),
        "corroboration_gap_weight": d("0.200000"),
        "contradiction_pressure_weight": d("0.250000"),
        "extraction_confidence_gap_weight": d("0.150000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchSourceRealTimeEventUpdatePressureConfig(**values)


def observation(
    pressure_group: str,
    *,
    authority_tier: str = "official_primary",
    observed_at: datetime = GENERATED_AT - timedelta(minutes=5),
    updates_in_window: Decimal = d("1.000000"),
    update_window_seconds: Decimal = d("3600.000000"),
    corroborating_source_count: Decimal = d("3.000000"),
    required_corroborating_source_count: Decimal = d("3.000000"),
    contradiction_count: Decimal = d("0.000000"),
    checked_claim_count: Decimal = d("10.000000"),
    extraction_confidence_score: Decimal = d("0.950000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchSourceRealTimeEventUpdatePressureObservation(
        pressure_group=pressure_group,
        authority_tier=authority_tier,
        observed_at=observed_at,
        updates_in_window=updates_in_window,
        update_window_seconds=update_window_seconds,
        corroborating_source_count=corroborating_source_count,
        required_corroborating_source_count=required_corroborating_source_count,
        contradiction_count=contradiction_count,
        checked_claim_count=checked_claim_count,
        extraction_confidence_score=extraction_confidence_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    *observations: object,
    generated_at: datetime = GENERATED_AT,
    cfg: object | None = None,
) -> Any:
    module = api()
    return module.build_research_source_real_time_event_update_pressure_report(
        observations,
        config=cfg or config(),
        generated_at=generated_at,
    )


def assert_decimal_public_numbers(value: object) -> None:
    for field in fields(value):
        if field.name in {
            "pressure_group",
            "rows",
            "reason_code_counts",
            "reason_codes",
            "status",
        }:
            continue
        if field.name.endswith("_status"):
            continue
        field_value = getattr(value, field.name)
        if isinstance(field_value, bool) or field_value is None:
            continue
        if any(
            marker in field.name
            for marker in (
                "age",
                "count",
                "score",
                "pressure",
                "velocity",
                "confidence",
                "weight",
            )
        ):
            assert type(field_value) is Decimal, field.name


def assert_no_json_numbers(value: Any) -> None:
    if type(value) in (float, int):
        raise AssertionError(f"payload numeric was not serialized as string: {value!r}")
    if isinstance(value, dict):
        for item_value in value.values():
            assert_no_json_numbers(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_json_numbers(item_value)


def assert_no_raw_public_surface(value: Any) -> None:
    forbidden_key_fragments = (
        "candidate",
        "condition_id",
        "database",
        "dsn",
        "market_id",
        "market_slug",
        "question",
        "raw",
        "recommendation",
        "sizing",
        "source_text",
        "source_url",
        "table",
        "token",
        "trade",
        "url",
        "wallet",
        "order",
    )
    forbidden_value_fragments = (
        "://",
        "www.",
        "candidate",
        "database",
        "dsn",
        "market_id",
        "market_slug",
        "order",
        "question",
        "raw",
        "source_text",
        "source_url",
        "token",
        "trade",
        "wallet",
    )
    if isinstance(value, dict):
        for key, item_value in value.items():
            lowered = key.lower()
            for fragment in forbidden_key_fragments:
                assert fragment not in lowered, key
            assert_no_raw_public_surface(item_value)
        return
    if isinstance(value, list):
        for item_value in value:
            assert_no_raw_public_surface(item_value)
        return
    if isinstance(value, str):
        lowered = value.lower()
        for fragment in forbidden_value_fragments:
            assert fragment not in lowered, value


def resign_payload(payload: dict[str, Any]) -> dict[str, Any]:
    unsigned = dict(payload)
    unsigned.pop("derived_validation_digest", None)
    signed = dict(unsigned)
    signed["derived_validation_digest"] = sha256(
        json.dumps(
            unsigned,
            allow_nan=False,
            separators=(",", ":"),
            sort_keys=True,
        ).encode("utf-8"),
    ).hexdigest()
    return signed


def row_by_group(built: object) -> dict[str, object]:
    return {row.pressure_group: row for row in built.rows}


def test_update_pressure_scoring_produces_pass_watch_and_block_rows() -> None:
    built = report(
        observation("event_alpha"),
        observation(
            "event_beta",
            authority_tier="verified_secondary",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            updates_in_window=d("5.000000"),
            corroborating_source_count=d("2.000000"),
            required_corroborating_source_count=d("3.000000"),
            contradiction_count=d("2.000000"),
            checked_claim_count=d("10.000000"),
            extraction_confidence_score=d("0.700000"),
        ),
        observation(
            "event_gamma",
            authority_tier="unverified_social",
            observed_at=GENERATED_AT - timedelta(hours=2),
            updates_in_window=d("10.000000"),
            corroborating_source_count=d("1.000000"),
            required_corroborating_source_count=d("4.000000"),
            contradiction_count=d("5.000000"),
            checked_claim_count=d("10.000000"),
            extraction_confidence_score=d("0.500000"),
        ),
    )
    rows = row_by_group(built)

    assert built.status == "block"
    assert built.row_count == d("3.000000")
    assert built.pass_count == d("1.000000")
    assert built.watch_count == d("1.000000")
    assert built.block_count == d("1.000000")
    assert built.max_pressure_score == rows["event_gamma"].pressure_score
    assert rows["event_alpha"].status == "pass"
    assert rows["event_alpha"].update_velocity_per_hour == d("1.000000")
    assert rows["event_alpha"].authority_tier_score == d("1.000000")
    assert rows["event_alpha"].pressure_score == d("0.038750")
    assert rows["event_beta"].status == "watch"
    assert rows["event_beta"].update_velocity_status == "watch"
    assert rows["event_beta"].authority_tier_status == "watch"
    assert rows["event_beta"].corroboration_status == "watch"
    assert rows["event_beta"].contradiction_status == "watch"
    assert rows["event_beta"].extraction_confidence_status == "watch"
    assert rows["event_gamma"].status == "block"
    assert rows["event_gamma"].stale_update_status == "block"
    assert rows["event_gamma"].pressure_score == d("0.750000")
    assert rows["event_gamma"].reason_codes == (
        "stale_update_block",
        "update_velocity_block",
        "authority_tier_block",
        "corroboration_block",
        "contradiction_pressure_block",
        "extraction_confidence_block",
        "pressure_score_block",
    )
    assert tuple(row.reason_code for row in built.reason_code_counts) == (
        "stale_update_pass",
        "stale_update_watch",
        "stale_update_block",
        "update_velocity_pass",
        "update_velocity_watch",
        "update_velocity_block",
        "authority_tier_pass",
        "authority_tier_watch",
        "authority_tier_block",
        "corroboration_pass",
        "corroboration_watch",
        "corroboration_block",
        "contradiction_pressure_pass",
        "contradiction_pressure_watch",
        "contradiction_pressure_block",
        "extraction_confidence_pass",
        "extraction_confidence_watch",
        "extraction_confidence_block",
        "pressure_score_pass",
        "pressure_score_watch",
        "pressure_score_block",
    )
    assert_decimal_public_numbers(built)
    for row in built.rows:
        assert_decimal_public_numbers(row)


def test_stale_and_contradictory_boundaries_are_watch_then_block() -> None:
    built = report(
        observation(
            "boundary_watch",
            observed_at=GENERATED_AT - timedelta(seconds=3600),
            updates_in_window=d("4.000000"),
            contradiction_count=d("4.000000"),
            checked_claim_count=d("10.000000"),
            extraction_confidence_score=d("0.800000"),
        ),
        observation(
            "boundary_block",
            observed_at=GENERATED_AT - timedelta(seconds=3600, microseconds=1),
            updates_in_window=d("8.000000"),
            contradiction_count=d("5.000000"),
            checked_claim_count=d("10.000000"),
            extraction_confidence_score=d("0.800000"),
        ),
    )
    rows = row_by_group(built)

    assert rows["boundary_watch"].latest_update_age_seconds == d("3600.000000")
    assert rows["boundary_watch"].stale_update_status == "watch"
    assert rows["boundary_watch"].update_velocity_status == "watch"
    assert rows["boundary_watch"].contradiction_status == "watch"
    assert rows["boundary_watch"].status == "watch"
    assert rows["boundary_block"].latest_update_age_seconds == d("3600.000001")
    assert rows["boundary_block"].stale_update_status == "block"
    assert rows["boundary_block"].update_velocity_status == "block"
    assert rows["boundary_block"].contradiction_status == "block"
    assert rows["boundary_block"].status == "block"


def test_public_payload_digest_is_deterministic_validated_and_json_safe() -> None:
    module = api()
    observations = (
        observation(
            "event_beta",
            authority_tier="verified_secondary",
            observed_at=GENERATED_AT - timedelta(minutes=20),
            updates_in_window=d("5.000000"),
            corroborating_source_count=d("2.000000"),
            required_corroborating_source_count=d("3.000000"),
            contradiction_count=d("2.000000"),
            checked_claim_count=d("10.000000"),
            extraction_confidence_score=d("0.700000"),
        ),
        observation("event_alpha"),
    )

    first = report(*observations)
    second = report(*reversed(observations))
    first_payload = first.public_payload

    assert first.derived_validation_digest == second.derived_validation_digest
    assert first.public_payload == second.public_payload
    assert first.payload == first_payload
    assert module.research_source_real_time_event_update_pressure_report_digest(first) == (
        first.derived_validation_digest
    )
    json.dumps(first_payload, allow_nan=False, sort_keys=True)
    assert first_payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert first_payload["row_count"] == "2.000000"
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.validate_research_source_real_time_event_update_pressure_public_payload(
        first_payload,
    )
    assert_no_json_numbers(first_payload)
    assert_no_raw_public_surface(first_payload)

    tampered = dict(first_payload)
    tampered["status"] = "pass"
    assert not module.validate_research_source_real_time_event_update_pressure_public_payload(
        tampered,
    )

    unsafe = dict(first_payload)
    unsafe["source_url"] = "https://example.invalid/raw"
    assert not module.validate_research_source_real_time_event_update_pressure_public_payload(
        unsafe,
    )

    invalid_numeric = dict(first_payload)
    invalid_numeric["row_count"] = "NaN"
    assert not module.validate_research_source_real_time_event_update_pressure_public_payload(
        resign_payload(invalid_numeric),
    )

    missing_nested_flags = dict(first_payload)
    missing_nested_flags["rows"] = [dict(row) for row in first_payload["rows"]]
    missing_nested_flags["rows"][0].pop("paper_only")
    assert not module.validate_research_source_real_time_event_update_pressure_public_payload(
        resign_payload(missing_nested_flags),
    )

    bad_nested_status = dict(first_payload)
    bad_nested_status["rows"] = [dict(row) for row in first_payload["rows"]]
    bad_nested_status["rows"][0]["update_velocity_status"] = "review"
    assert not module.validate_research_source_real_time_event_update_pressure_public_payload(
        resign_payload(bad_nested_status),
    )


def test_dataclasses_are_frozen_strict_and_reject_leaky_or_live_surfaces() -> None:
    module = api()
    built = report(observation("event_alpha"))

    public_classes = (
        module.ResearchSourceRealTimeEventUpdatePressureConfig,
        module.ResearchSourceRealTimeEventUpdatePressureObservation,
        module.ResearchSourceRealTimeEventUpdatePressureReasonCodeCount,
        module.ResearchSourceRealTimeEventUpdatePressureRow,
        module.ResearchSourceRealTimeEventUpdatePressureReport,
    )
    for public_class in public_classes:
        assert is_dataclass(public_class)
        assert public_class.__dataclass_params__.frozen is True

    with pytest.raises(FrozenInstanceError):
        built.status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadReport(module.ResearchSourceRealTimeEventUpdatePressureReport):
            pass

    with pytest.raises(ValueError, match="updates_in_window must be exactly Decimal"):
        observation("event_alpha", updates_in_window=1)  # type: ignore[arg-type]

    with pytest.raises(ValueError, match="checked_claim_count must be exactly Decimal"):
        observation("event_alpha", checked_claim_count=_DecimalSubclass("1.000000"))

    with pytest.raises(ValueError, match="generated_at must be exactly datetime"):
        report(
            observation("event_alpha"),
            generated_at=_DatetimeSubclass(2026, 7, 8, 12, tzinfo=UTC),
        )

    with pytest.raises(ValueError, match="timezone-aware"):
        observation("event_alpha", observed_at=datetime(2026, 7, 8, 11, 55))

    with pytest.raises(ValueError, match="unsafe"):
        observation("market_slug_candidate_raw")

    with pytest.raises(ValueError, match="unsupported authority_tier"):
        observation("event_alpha", authority_tier="anonymous_forum")

    with pytest.raises(ValueError, match="report_only"):
        observation("event_alpha", report_only=False)

    with pytest.raises(ValueError, match="readonly"):
        replace(built, readonly=False)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(built, row_count=d("9.000000"))

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_roots: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_roots.update(alias.name.split(".")[0] for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module:
            imported_roots.add(node.module.split(".")[0])

    forbidden_imports = {
        "httpx",
        "psycopg",
        "py_clob_client",
        "requests",
        "socket",
        "sqlalchemy",
        "sqlite3",
        "web3",
    }
    assert imported_roots.isdisjoint(forbidden_imports)
    public_names = set(dir(module))
    forbidden_public_names = {
        "auth",
        "client",
        "database",
        "dsn",
        "live",
        "order",
        "recommendation",
        "sizing",
        "table",
        "token",
        "trade",
        "wallet",
    }
    assert public_names.isdisjoint(forbidden_public_names)


def test_custom_config_validation_changes_status_and_rejects_bad_shapes() -> None:
    module = api()
    strict = config(
        max_pass_update_age_seconds=d("120.000000"),
        max_watch_update_age_seconds=d("240.000000"),
        watch_update_velocity_per_hour=d("2.000000"),
        block_update_velocity_per_hour=d("4.000000"),
        max_pass_pressure_score=d("0.030000"),
        max_watch_pressure_score=d("0.080000"),
    )
    built = report(observation("event_alpha"), cfg=strict)

    assert built.status == "block"
    assert row_by_group(built)["event_alpha"].pressure_score_status == "watch"
    assert row_by_group(built)["event_alpha"].stale_update_status == "block"

    with pytest.raises(ValueError, match="block_update_velocity_per_hour"):
        config(block_update_velocity_per_hour=d("4.000000"), watch_update_velocity_per_hour=d("4.000000"))

    with pytest.raises(ValueError, match="corroboration"):
        config(min_watch_corroboration_score=d("0.800000"))

    with pytest.raises(ValueError, match="weight"):
        config(update_velocity_weight=d("0.500000"))

    with pytest.raises(ValueError, match="paper_only"):
        config(paper_only=False)

    assert module.REAL_TIME_EVENT_UPDATE_PRESSURE_STATUSES == (
        "pass",
        "watch",
        "block",
    )
