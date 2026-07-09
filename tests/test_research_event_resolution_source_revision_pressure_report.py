from __future__ import annotations

import ast
import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
RECENT_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)
STALE_AT = datetime(2026, 7, 8, 11, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _api():
    return import_module(
        "polymarket_alpha_lab.research_event_resolution_source_revision_pressure_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _config(**overrides: object):
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_REVISION_PRESSURE_REPORT_CONFIG_VERSION
        ),
        "watch_revision_count": d("2.000000"),
        "block_revision_count": d("4.000000"),
        "watch_contradiction_revision_count": d("1.000000"),
        "block_contradiction_revision_count": d("2.000000"),
        "watch_material_revision_score": d("0.250000"),
        "block_material_revision_score": d("0.600000"),
        "watch_origin_drift_score": d("0.250000"),
        "block_origin_drift_score": d("0.600000"),
        "max_unreviewed_revision_age_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return api.ResearchEventResolutionSourceRevisionPressureConfig(**values)


def _observation(
    event_key: str = "event-alpha",
    revision_key: str = "revision-alpha",
    *,
    source_family: str = "official",
    revision_count: Decimal = ZERO,
    contradiction_revision_count: Decimal = ZERO,
    material_revision_score: Decimal = ZERO,
    origin_drift_score: Decimal = ZERO,
    observed_at: datetime = RECENT_AT,
    review_completed: bool = True,
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
):
    api = _api()
    return api.ResearchEventResolutionSourceRevisionPressureInput(
        event_key=event_key,
        revision_key=revision_key,
        source_family=source_family,
        revision_count=revision_count,
        contradiction_revision_count=contradiction_revision_count,
        material_revision_score=material_revision_score,
        origin_drift_score=origin_drift_score,
        observed_at=observed_at,
        review_completed=review_completed,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _report(
    rows: tuple[object, ...],
    *,
    cfg=None,
    generated_at: datetime = GENERATED_AT,
):
    api = _api()
    return api.build_research_event_resolution_source_revision_pressure_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_source_revision_pressure_classifies_pass_watch_and_block_rows() -> None:
    api = _api()
    report = _report(
        (
            _observation(
                "event-block",
                "revision-block",
                revision_count=d("4.000000"),
                contradiction_revision_count=d("2.000000"),
                material_revision_score=d("0.650000"),
                origin_drift_score=d("0.700000"),
                observed_at=STALE_AT,
                review_completed=False,
            ),
            _observation(
                "event-watch",
                "revision-watch",
                source_family="proxy",
                revision_count=d("2.000000"),
                material_revision_score=d("0.300000"),
                observed_at=GENERATED_AT - timedelta(minutes=15),
            ),
            _observation(
                "event-pass",
                "revision-pass",
                observed_at=GENERATED_AT - timedelta(minutes=5),
            ),
        ),
        generated_at=datetime(2026, 7, 9, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is api.ResearchEventResolutionSourceRevisionPressureReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.revision_observation_count == d("3.000000")
    assert report.pass_count == d("1.000000")
    assert report.watch_count == d("1.000000")
    assert report.block_count == d("1.000000")
    assert report.pressure_event_count == d("2.000000")
    assert report.review_required_count == d("2.000000")
    assert report.missing_review_count == d("1.000000")
    assert report.max_revision_count == d("4.000000")
    assert report.max_contradiction_revision_count == d("2.000000")
    assert report.max_material_revision_score == d("0.650000")
    assert report.max_origin_drift_score == d("0.700000")
    assert report.max_pressure_score == d("1.000000")
    assert report.max_revision_age_seconds == d("90000.000000")
    assert report.watch_ratio == d("0.666667")
    assert report.block_ratio == d("0.333333")
    assert report.status == "block"
    assert report.reason_codes == (
        "revision_count_pressure_present",
        "contradiction_revision_pressure_present",
        "material_revision_pressure_present",
        "origin_drift_pressure_present",
        "source_revision_review_required_present",
        "missing_source_revision_review_present",
        "source_revision_pressure_block_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert block_row == api.ResearchEventResolutionSourceRevisionPressureRow(
        event_key="event-block",
        revision_key="revision-block",
        source_family="official",
        status="block",
        revision_count=d("4.000000"),
        contradiction_revision_count=d("2.000000"),
        material_revision_score=d("0.650000"),
        origin_drift_score=d("0.700000"),
        pressure_score=d("1.000000"),
        revision_age_seconds=d("90000.000000"),
        review_required=True,
        missing_review=True,
        reason_codes=(
            "revision_count_block",
            "contradiction_revision_block",
            "material_revision_block",
            "origin_drift_block",
            "source_revision_review_required",
            "missing_source_revision_review",
            "stale_unreviewed_source_revision_block",
        ),
    )
    assert watch_row.event_key == "event-watch"
    assert watch_row.status == "watch"
    assert watch_row.pressure_score == d("0.500000")
    assert watch_row.reason_codes == (
        "revision_count_watch",
        "material_revision_watch",
        "source_revision_review_required",
    )
    assert pass_row.event_key == "event-pass"
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("source_revision_pressure_clear",)


def test_stale_missing_review_escalates_watch_level_revision_to_block() -> None:
    report = _report(
        (
            _observation(
                "event-stale-watch",
                "revision-stale-watch",
                material_revision_score=d("0.300000"),
                observed_at=STALE_AT,
                review_completed=False,
            ),
        ),
    )

    (row,) = report.rows
    assert row.status == "block"
    assert row.reason_codes == (
        "material_revision_watch",
        "source_revision_review_required",
        "missing_source_revision_review",
        "stale_unreviewed_source_revision_block",
    )
    assert report.block_count == ONE
    assert report.watch_count == ZERO
    assert report.status == "block"


def test_empty_and_clear_reports_are_pass_decimal_json_ready_and_digest_validated() -> None:
    api = _api()
    empty = _report(())
    clear = _report((_observation("event-clear", "revision-clear"),))

    assert empty.revision_observation_count == ZERO
    assert empty.watch_ratio == ZERO
    assert empty.block_ratio == ZERO
    assert empty.status == "pass"
    assert empty.reason_codes == ("source_revision_pressure_clear",)
    assert empty.rows == ()

    payload = api.research_event_resolution_source_revision_pressure_report_payload(clear)
    repeat_payload = api.research_event_resolution_source_revision_pressure_report_payload(clear)

    assert clear.revision_observation_count == ONE
    assert clear.pass_count == ONE
    assert clear.status == "pass"
    assert clear.reason_codes == ("source_revision_pressure_clear",)
    assert payload == repeat_payload
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["revision_observation_count"] == "1.000000"
    assert payload["watch_ratio"] == "0.000000"
    assert payload["rows"][0]["event_key"] == "event-clear"
    assert payload["rows"][0]["pressure_score"] == "0.000000"
    assert payload["derived_validation_digest"] == clear.derived_validation_digest
    assert len(clear.derived_validation_digest) == 64
    assert int(clear.derived_validation_digest, 16) >= 0
    assert json.dumps(payload, sort_keys=True) == json.dumps(repeat_payload, sort_keys=True)
    assert api.validate_research_event_resolution_source_revision_pressure_report_payload(
        payload,
    )
    assert not _contains_float_or_int(payload)
    assert not _has_forbidden_public_surface(payload)

    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    encoded = json.dumps(
        digest_payload,
        ensure_ascii=True,
        separators=(",", ":"),
        sort_keys=True,
    )
    assert hashlib.sha256(encoded.encode("utf-8")).hexdigest() == (
        clear.derived_validation_digest
    )


def test_validation_rejects_bad_types_times_flags_sensitive_values_and_digest() -> None:
    api = _api()
    report = _report((_observation("event-tamper", "revision-tamper"),))

    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="watch_revision_count"):
        _config(watch_revision_count=d("4.000000"))
    with pytest.raises(ValueError, match="block_material_revision_score"):
        _config(block_material_revision_score=_DecimalSubclass("0.600000"))
    with pytest.raises(ValueError, match="generated_at"):
        _report((_observation("event-naive-report", "revision-naive-report"),), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            "event-naive",
            "revision-naive",
            observed_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at"):
        _observation(
            "event-none-offset",
            "revision-none-offset",
            observed_at=datetime(2026, 7, 9, 12, 0, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at must not be after generated_at"):
        _report(
            (
                _observation(
                    "event-future",
                    "revision-future",
                    observed_at=GENERATED_AT + timedelta(seconds=1),
                ),
            ),
        )
    with pytest.raises(ValueError, match="revision_count"):
        _observation("event-count", "revision-count", revision_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="review_completed"):
        _observation("event-review", "revision-review", review_completed=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="paper_only"):
        _observation("event-flag", "revision-flag", paper_only=False)

    for unsafe_value in (
        _join_parts("market", "_", "id"),
        _join_parts("market", "_", "slug"),
        _join_parts("candidate", "_", "id"),
        _join_parts("source", "_", "url"),
        _join_parts("source", "_", "text"),
        "https://example.invalid/source",
        "postgres://example.invalid/db",
        _join_parts("wall", "et"),
        _join_parts("or", "der"),
        _join_parts("to", "ken"),
    ):
        with pytest.raises(ValueError, match="unsafe public value"):
            _observation(unsafe_value, "revision-unsafe")

    unsafe_payload = api.research_event_resolution_source_revision_pressure_report_payload(report)
    unsafe_payload["source_url"] = "https://example.invalid/source"
    with pytest.raises(ValueError, match="unsafe public payload"):
        api.validate_research_event_resolution_source_revision_pressure_report_payload(
            unsafe_payload,
        )


def test_module_has_no_external_action_or_sensitive_surfaces() -> None:
    api = _api()
    source = inspect.getsource(api).lower()
    tree = ast.parse(source)

    assert "float(" not in source
    assert ".total_seconds(" not in source
    for term in (
        _join_parts("data", "base"),
        _join_parts("net", "work"),
        _join_parts("li", "ve"),
        _join_parts("au", "th"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "end"),
    ):
        assert term not in source

    imported_modules: set[str] = set()
    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.update(alias.name for alias in node.names)
        if isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.add(node.module)
        if isinstance(node, ast.Constant):
            assert type(node.value) is not float
        if isinstance(node, ast.Call):
            call_name = getattr(node.func, "attr", getattr(node.func, "id", ""))
            assert call_name not in {
                "connect",
                "execute",
                "executemany",
                "open",
                "request",
                "post",
                "put",
                "patch",
                "delete",
            }

    forbidden_import_fragments = (
        "cli",
        "db",
        "env",
        "httpx",
        "psycopg",
        "requests",
        "socket",
        "subprocess",
        "urllib",
        "web3",
    )
    assert not any(
        fragment in imported_module.lower()
        for imported_module in imported_modules
        for fragment in forbidden_import_fragments
    )

    exposed_names = {
        field.name
        for field in fields(api.ResearchEventResolutionSourceRevisionPressureReport)
    }
    assert _join_parts("candidate", "_", "id") not in exposed_names
    assert _join_parts("market", "_", "id") not in exposed_names
    assert _join_parts("market", "_", "slug") not in exposed_names
    assert _join_parts("que", "stion") not in exposed_names


def _contains_float_or_int(value: object) -> bool:
    if isinstance(value, bool):
        return False
    if isinstance(value, float | int):
        return True
    if isinstance(value, dict):
        return any(_contains_float_or_int(item) for item in value.values())
    if isinstance(value, list | tuple):
        return any(_contains_float_or_int(item) for item in value)
    return False


def _has_forbidden_public_surface(value: object) -> bool:
    rendered = repr(value).lower()
    forbidden_terms = (
        _join_parts("raw", "_", "candidate"),
        _join_parts("candidate", "_", "id"),
        _join_parts("market", "_", "id"),
        _join_parts("market", "_", "slug"),
        "slug",
        _join_parts("que", "stion"),
        _join_parts("source", "_", "url"),
        _join_parts("source", "_", "text"),
        "dsn",
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wall", "et"),
        _join_parts("or", "der"),
        _join_parts("tra", "de"),
        "http://",
        "https://",
        "://",
    )
    return any(term in rendered for term in forbidden_terms)
