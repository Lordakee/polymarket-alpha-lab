from __future__ import annotations

import ast
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from hashlib import sha256
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab.research_event_source_resolution_clock_drift_report"
)
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_source_resolution_clock_drift_report.py"
)
GENERATED_AT = datetime(2026, 7, 8, 18, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


def api():
    return import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object):
    module = api()
    values: dict[str, object] = {
        "config_version": (
            module.DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_CLOCK_DRIFT_REPORT_CONFIG_VERSION
        ),
        "watch_clock_drift_seconds_threshold": d("300.000000"),
        "block_clock_drift_seconds_threshold": d("3600.000000"),
        "watch_source_lag_seconds_threshold": d("1800.000000"),
        "block_source_lag_seconds_threshold": d("7200.000000"),
        "watch_clock_drift_score_threshold": d("0.250000"),
        "block_clock_drift_score_threshold": d("0.600000"),
        "paper_only": True,
        "report_only": True,
        "readonly": True,
    }
    values.update(overrides)
    return module.ResearchEventSourceResolutionClockDriftConfig(**values)


def sample(
    scope: str,
    *,
    events: str,
    expected_resolution_at: datetime,
    observed_resolution_at: datetime,
    evidence_observed_at: datetime,
):
    module = api()
    return module.ResearchEventSourceResolutionClockDriftSample(
        event_scope=scope,
        event_count=d(events),
        expected_resolution_at=expected_resolution_at,
        observed_resolution_at=observed_resolution_at,
        evidence_observed_at=evidence_observed_at,
    )


def report(*samples: object, cfg: object | None = None):
    module = api()
    return module.build_research_event_source_resolution_clock_drift_report(
        samples,
        config=cfg or config(),
        generated_at=GENERATED_AT,
    )


def test_empty_report_blocks_with_hard_flags_and_zero_metrics() -> None:
    module = api()
    drift_report = report()

    assert type(drift_report) is module.ResearchEventSourceResolutionClockDriftReport
    assert is_dataclass(drift_report)
    assert drift_report.__dataclass_params__.frozen is True
    assert drift_report.generated_at == GENERATED_AT
    assert drift_report.config_version == (
        module.DEFAULT_RESEARCH_EVENT_SOURCE_RESOLUTION_CLOCK_DRIFT_REPORT_CONFIG_VERSION
    )
    assert drift_report.sample_count == ZERO
    assert drift_report.event_count == ZERO
    assert drift_report.drifted_event_count == ZERO
    assert drift_report.stale_source_event_count == ZERO
    assert drift_report.pass_count == ZERO
    assert drift_report.watch_count == ZERO
    assert drift_report.block_count == ZERO
    assert drift_report.max_clock_drift_seconds == ZERO
    assert drift_report.weighted_average_clock_drift_seconds == ZERO
    assert drift_report.max_source_lag_seconds == ZERO
    assert drift_report.weighted_average_source_lag_seconds == ZERO
    assert drift_report.clock_drift_pressure_ratio == ZERO
    assert drift_report.source_lag_pressure_ratio == ZERO
    assert drift_report.average_clock_drift_ratio == ZERO
    assert drift_report.average_source_lag_ratio == ZERO
    assert drift_report.clock_drift_score == ZERO
    assert drift_report.status == "block"
    assert drift_report.reason_codes == (
        "no_event_source_resolution_clock_drift_samples",
    )
    assert drift_report.rows == ()
    assert drift_report.paper_only is True
    assert drift_report.report_only is True
    assert drift_report.readonly is True
    assert len(drift_report.derived_validation_digest) == 64


def test_rolls_up_clock_drift_and_lag_pressure_without_raw_surfaces() -> None:
    module = api()
    drift_report = report(
        sample(
            "event-alpha",
            events="3.000000",
            expected_resolution_at=GENERATED_AT + timedelta(hours=4),
            observed_resolution_at=GENERATED_AT + timedelta(hours=4, minutes=10),
            evidence_observed_at=GENERATED_AT - timedelta(minutes=5),
        ),
        sample(
            "event-beta",
            events="2.000000",
            expected_resolution_at=GENERATED_AT + timedelta(hours=4),
            observed_resolution_at=GENERATED_AT + timedelta(hours=5, minutes=30),
            evidence_observed_at=GENERATED_AT - timedelta(hours=2),
        ),
        sample(
            "event-clear",
            events="1.000000",
            expected_resolution_at=GENERATED_AT + timedelta(hours=4),
            observed_resolution_at=GENERATED_AT + timedelta(hours=4),
            evidence_observed_at=GENERATED_AT - timedelta(minutes=1),
        ),
    )

    payload = module.research_event_source_resolution_clock_drift_report_payload(
        drift_report,
    )
    repeat_payload = module.research_event_source_resolution_clock_drift_report_payload(
        drift_report,
    )

    assert drift_report.status == "block"
    assert drift_report.sample_count == d("3.000000")
    assert drift_report.event_count == d("6.000000")
    assert drift_report.drifted_event_count == d("5.000000")
    assert drift_report.stale_source_event_count == d("2.000000")
    assert drift_report.pass_count == d("1.000000")
    assert drift_report.watch_count == d("1.000000")
    assert drift_report.block_count == d("1.000000")
    assert drift_report.max_clock_drift_seconds == d("5400.000000")
    assert drift_report.weighted_average_clock_drift_seconds == d("2100.000000")
    assert drift_report.max_source_lag_seconds == d("7200.000000")
    assert drift_report.weighted_average_source_lag_seconds == d("2560.000000")
    assert drift_report.clock_drift_pressure_ratio == d("0.833333")
    assert drift_report.source_lag_pressure_ratio == d("0.333333")
    assert drift_report.average_clock_drift_ratio == d("0.583333")
    assert drift_report.average_source_lag_ratio == d("0.355556")
    assert drift_report.clock_drift_score == d("0.526389")
    assert drift_report.reason_codes == (
        "clock_drift_pressure_watch",
        "source_lag_pressure_watch",
        "event_source_resolution_clock_drift_sample_block",
    )
    assert tuple(row.event_scope for row in drift_report.rows) == (
        "event-alpha",
        "event-beta",
        "event-clear",
    )
    assert tuple(row.status for row in drift_report.rows) == (
        "watch",
        "block",
        "pass",
    )
    assert drift_report.rows[1].reason_codes == (
        "clock_drift_block",
        "source_lag_block",
    )
    assert payload == repeat_payload
    assert payload["derived_validation_digest"] == (
        drift_report.derived_validation_digest
    )
    assert payload["rows"][1]["clock_drift_seconds"] == "5400.000000"
    assert payload["rows"][1]["source_lag_seconds"] == "7200.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not _has_forbidden_public_surface(payload)
    assert not any(type(value) in (float, int) for value in _walk_payload_values(payload))
    assert json.dumps(payload, sort_keys=True, separators=(",", ":")) == (
        module.serialize_research_event_source_resolution_clock_drift_report_payload(
            drift_report,
        )
    )
    assert module.validate_research_event_source_resolution_clock_drift_report_payload(
        payload,
    )


def test_pass_report_and_payload_digest_are_deterministic() -> None:
    module = api()
    drift_report = report(
        sample(
            "event-clear",
            events="4.000000",
            expected_resolution_at=GENERATED_AT + timedelta(days=1),
            observed_resolution_at=GENERATED_AT + timedelta(days=1),
            evidence_observed_at=GENERATED_AT,
        ),
    )

    assert drift_report.status == "pass"
    assert drift_report.reason_codes == (
        "event_source_resolution_clock_drift_pass",
    )
    assert drift_report.clock_drift_score == ZERO
    assert type(drift_report.derived_validation_digest) is str
    assert len(drift_report.derived_validation_digest) == 64
    assert int(drift_report.derived_validation_digest, 16) >= 0
    assert report(*drift_report.source_samples).derived_validation_digest == (
        drift_report.derived_validation_digest
    )

    payload = module.research_event_source_resolution_clock_drift_report_payload(
        drift_report,
    )
    assert payload["event_count"] == "4.000000"
    assert payload["rows"][0]["clock_drift_ratio"] == "0.000000"
    assert (
        module.research_event_source_resolution_clock_drift_report_payload_digest(
            payload,
        )
        == drift_report.derived_validation_digest
    )
    assert (
        module.research_event_source_resolution_clock_drift_report_payload(payload)
        == payload
    )


def test_digest_is_sha256_of_canonical_public_payload_without_digest_fields() -> None:
    module = api()
    drift_report = report(
        sample(
            "event-clear",
            events="4.000000",
            expected_resolution_at=GENERATED_AT + timedelta(days=1),
            observed_resolution_at=GENERATED_AT + timedelta(days=1),
            evidence_observed_at=GENERATED_AT,
        ),
    )
    payload = module.research_event_source_resolution_clock_drift_report_payload(
        drift_report,
    )
    canonical_payload = _without_digest_fields(payload)
    canonical_json = json.dumps(
        canonical_payload,
        sort_keys=True,
        separators=(",", ":"),
    )

    assert sha256(canonical_json.encode("utf-8")).hexdigest() == (
        drift_report.derived_validation_digest
    )


def test_public_payload_validation_rejects_root_and_nested_schema_drift() -> None:
    module = api()
    payload = module.research_event_source_resolution_clock_drift_report_payload(
        report(
            sample(
                "event-clear",
                events="4.000000",
                expected_resolution_at=GENERATED_AT + timedelta(days=1),
                observed_resolution_at=GENERATED_AT + timedelta(days=1),
                evidence_observed_at=GENERATED_AT,
            ),
        ),
    )

    extra_root = _payload_copy(payload)
    extra_root["unexpected_metric"] = "0.000000"
    extra_root = _redigest_payload(module, extra_root)
    with pytest.raises(ValueError, match="report payload schema"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            extra_root,
        )

    missing_root = _payload_copy(payload)
    del missing_root["status"]
    missing_root = _redigest_payload(module, missing_root)
    with pytest.raises(ValueError, match="report payload schema"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            missing_root,
        )

    extra_row = _payload_copy(payload)
    extra_row["rows"][0]["unexpected_metric"] = "0.000000"
    extra_row = _redigest_payload(module, extra_row)
    with pytest.raises(ValueError, match="row payload schema"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            extra_row,
        )

    missing_sample = _payload_copy(payload)
    del missing_sample["source_samples"][0]["expected_resolution_at"]
    missing_sample = _redigest_payload(module, missing_sample)
    with pytest.raises(ValueError, match="sample payload schema"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            missing_sample,
        )


def test_public_payload_validation_rejects_noncanonical_and_inconsistent_values() -> None:
    module = api()
    payload = module.research_event_source_resolution_clock_drift_report_payload(
        report(
            sample(
                "event-clear",
                events="4.000000",
                expected_resolution_at=GENERATED_AT + timedelta(days=1),
                observed_resolution_at=GENERATED_AT + timedelta(days=1),
                evidence_observed_at=GENERATED_AT,
            ),
        ),
    )

    noncanonical_decimal = _payload_copy(payload)
    noncanonical_decimal["event_count"] = "4"
    noncanonical_decimal = _redigest_payload(module, noncanonical_decimal)
    with pytest.raises(ValueError, match="canonical Decimal string"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            noncanonical_decimal,
        )

    noncanonical_datetime = _payload_copy(payload)
    noncanonical_datetime["generated_at"] = "2026-07-08 18:00:00+00:00"
    noncanonical_datetime = _redigest_payload(module, noncanonical_datetime)
    with pytest.raises(ValueError, match="canonical UTC datetime"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            noncanonical_datetime,
        )

    invalid_status = _payload_copy(payload)
    invalid_status["status"] = "unknown"
    invalid_status = _redigest_payload(module, invalid_status)
    with pytest.raises(ValueError, match="status"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            invalid_status,
        )

    invalid_thresholds = _payload_copy(payload)
    invalid_thresholds["watch_clock_drift_seconds_threshold"] = "3600.000000"
    invalid_thresholds["block_clock_drift_seconds_threshold"] = "300.000000"
    invalid_thresholds = _redigest_payload(module, invalid_thresholds)
    with pytest.raises(
        ValueError,
        match="block_clock_drift_seconds_threshold.*exceed",
    ):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            invalid_thresholds,
        )

    inconsistent_row = _payload_copy(payload)
    inconsistent_row["rows"][0]["event_count"] = "5.000000"
    inconsistent_row = _redigest_payload(module, inconsistent_row)
    with pytest.raises(ValueError, match="event_count|source_samples"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            inconsistent_row,
        )

    inconsistent_sample = _payload_copy(payload)
    inconsistent_sample["source_samples"][0]["observed_resolution_at"] = (
        GENERATED_AT + timedelta(days=1, minutes=15)
    ).isoformat()
    inconsistent_sample = _redigest_payload(module, inconsistent_sample)
    with pytest.raises(ValueError, match="rows must match source_samples"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            inconsistent_sample,
        )


def test_validation_rejects_bad_inputs_flags_and_unsafe_payloads() -> None:
    module = api()
    clear = report(
        sample(
            "event-clear",
            events="1.000000",
            expected_resolution_at=GENERATED_AT,
            observed_resolution_at=GENERATED_AT,
            evidence_observed_at=GENERATED_AT,
        ),
    )
    payload = module.research_event_source_resolution_clock_drift_report_payload(clear)

    with pytest.raises(FrozenInstanceError):
        clear.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        clear.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="status must match rows"):
        replace(clear, status="watch", derived_validation_digest="")
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(clear, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="paper_only"):
        replace(config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        module.ResearchEventSourceResolutionClockDriftSample(
            event_scope="event-clear",
            event_count=1,  # type: ignore[arg-type]
            expected_resolution_at=GENERATED_AT,
            observed_resolution_at=GENERATED_AT,
            evidence_observed_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="timezone-aware"):
        sample(
            "event-clear",
            events="1.000000",
            expected_resolution_at=datetime(2026, 7, 8, 18, 0),
            observed_resolution_at=GENERATED_AT,
            evidence_observed_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="after generated_at"):
        report(
            sample(
                "event-clear",
                events="1.000000",
                expected_resolution_at=GENERATED_AT,
                observed_resolution_at=GENERATED_AT,
                evidence_observed_at=GENERATED_AT + timedelta(seconds=1),
            ),
        )
    with pytest.raises(ValueError, match="event_scope"):
        sample(
            "market-slug-leak",
            events="1.000000",
            expected_resolution_at=GENERATED_AT,
            observed_resolution_at=GENERATED_AT,
            evidence_observed_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="watch_clock_drift_seconds_threshold"):
        config(watch_clock_drift_seconds_threshold=_DecimalSubclass("300.000000"))
    with pytest.raises(ValueError, match="block_clock_drift_seconds_threshold"):
        config(block_clock_drift_seconds_threshold=d("300.000000"))
    with pytest.raises(ValueError, match="paper_only"):
        module.research_event_source_resolution_clock_drift_report_payload(
            {**payload, "paper_only": False},
        )
    missing_flag_payload = dict(payload)
    del missing_flag_payload["paper_only"]
    missing_flag_payload["derived_validation_digest"] = module._derived_digest(
        missing_flag_payload,
    )
    with pytest.raises(ValueError, match="paper_only"):
        module.research_event_source_resolution_clock_drift_report_payload(
            missing_flag_payload,
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        module.research_event_source_resolution_clock_drift_report_payload(
            {**payload, "event_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        module.research_event_source_resolution_clock_drift_report_payload(
            {**payload, "clock_drift_score": 0.1},
        )
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_source_resolution_clock_drift_report_payload(
            {
                "source_" + "url": "blocked",
                "paper_only": True,
                "report_only": True,
                "readonly": True,
            },
        )
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.research_event_source_resolution_clock_drift_report_payload(
            {**payload, "status": "watch"},
        )


def test_public_dataclasses_are_frozen_decimal_only_and_source_is_readonly() -> None:
    module = api()
    public_classes = (
        module.ResearchEventSourceResolutionClockDriftConfig,
        module.ResearchEventSourceResolutionClockDriftSample,
        module.ResearchEventSourceResolutionClockDriftRow,
        module.ResearchEventSourceResolutionClockDriftReport,
    )
    assert all(is_dataclass(public_class) for public_class in public_classes)
    assert all(public_class.__dataclass_params__.frozen is True for public_class in public_classes)
    for public_class in public_classes:
        for field in fields(public_class):
            if (
                field.name.endswith("_count")
                or field.name.endswith("_ratio")
                or field.name.endswith("_seconds")
            ):
                assert field.type in (Decimal, "Decimal")
            assert not any(term in field.name.lower() for term in _forbidden_terms())

    tree = ast.parse(MODULE_PATH.read_text(encoding="utf-8"))
    imported_modules = {
        alias.name.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.Import)
        for alias in node.names
    }
    imported_modules.update(
        node.module.split(".")[0]
        for node in ast.walk(tree)
        if isinstance(node, ast.ImportFrom) and node.module is not None
    )
    assert not (
        imported_modules
        & {
            "aiohttp",
            "ccxt",
            "httpx",
            "psycopg",
            "requests",
            "socket",
            "sqlite3",
            "sqlalchemy",
            "subprocess",
            "web3",
        }
    )


def _walk_payload_values(value: object) -> tuple[object, ...]:
    values: list[object] = []
    if isinstance(value, dict):
        for item in value.values():
            values.extend(_walk_payload_values(item))
    elif isinstance(value, list):
        for item in value:
            values.extend(_walk_payload_values(item))
    else:
        values.append(value)
    return tuple(values)


def _payload_copy(payload: dict[str, Any]) -> dict[str, Any]:
    copied = json.loads(json.dumps(payload))
    assert type(copied) is dict
    return copied


def _redigest_payload(module: Any, payload: dict[str, Any]) -> dict[str, Any]:
    for key in ("source_samples", "rows"):
        values = payload.get(key, [])
        if type(values) is list:
            for value in values:
                if type(value) is dict:
                    value["derived_validation_digest"] = module._derived_digest(value)
    payload["derived_validation_digest"] = module._derived_digest(payload)
    return payload


def _without_digest_fields(value: object) -> object:
    if type(value) is dict:
        return {
            key: _without_digest_fields(item)
            for key, item in value.items()
            if key != "derived_validation_digest"
        }
    if type(value) is list:
        return [_without_digest_fields(item) for item in value]
    return value


def _has_forbidden_public_surface(value: Any) -> bool:
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in _forbidden_terms()):
                return True
            if _has_forbidden_public_surface(item):
                return True
    if isinstance(value, list):
        return any(_has_forbidden_public_surface(item) for item in value)
    if isinstance(value, str):
        lowered = value.lower()
        return any(term in lowered for term in _forbidden_terms())
    return False


def _forbidden_terms() -> tuple[str, ...]:
    return (
        "candidate",
        "market_id",
        "market_slug",
        "slug",
        "question",
        "source_url",
        "source_text",
        "raw_text",
        "dsn",
        "table",
        "token",
        "wallet",
        "order",
        "trade",
        "sizing",
        "recommendation",
    )
