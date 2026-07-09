from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_event_authority_update_latency_floor_report"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 55, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _DatetimeSubclass(datetime):
    pass


def api() -> Any:
    return importlib.import_module(MODULE_NAME)


def d(value: str) -> Decimal:
    return Decimal(value)


def digest(value: str) -> str:
    return hashlib.sha256(value.encode("utf-8")).hexdigest()


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "pass_latency_floor_seconds": d("900.000000"),
        "watch_latency_floor_seconds": d("300.000000"),
    }
    values.update(overrides)
    return module.ResearchEventAuthorityUpdateLatencyFloorConfig(**values)


def observation(
    seed: str = "alpha",
    *,
    observed_at: datetime = OBSERVED_AT,
    authority_update_latency_seconds: Decimal = d("1200.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventAuthorityUpdateLatencyFloorObservation(
        event_digest=digest(f"{seed}-event"),
        authority_digest=digest(f"{seed}-authority"),
        observed_at=observed_at,
        authority_update_latency_seconds=authority_update_latency_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_authority_update_latency_floor_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=GENERATED_AT,
    )


def assert_no_numeric_objects(value: object) -> None:
    if isinstance(value, dict):
        for item in value.values():
            assert_no_numeric_objects(item)
        return
    if isinstance(value, list):
        for item in value:
            assert_no_numeric_objects(item)
        return
    assert type(value) not in (float, int)


def unsafe_terms() -> tuple[str, ...]:
    return (
        _join_parts("cand", "idate"),
        _join_parts("mark", "et"),
        _join_parts("sl", "ug"),
        _join_parts("que", "stion"),
        _join_parts("ur", "l"),
        _join_parts("te", "xt"),
        _join_parts("d", "sn"),
        _join_parts("ta", "ble"),
        _join_parts("to", "ken"),
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("li", "ve"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "endation"),
    )


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchEventAuthorityUpdateLatencyFloorReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.event_count == d("0.000000")
    assert report.pass_event_count == d("0.000000")
    assert report.watch_event_count == d("0.000000")
    assert report.block_event_count == d("0.000000")
    assert report.below_latency_floor_event_count == d("0.000000")
    assert report.minimum_authority_update_latency_seconds == d("0.000000")
    assert report.maximum_latency_floor_gap_seconds == d("0.000000")
    assert report.average_latency_floor_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_event_authority_update_latency_floor_empty",
    )
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_event_authority_update_latency_floor_report_digest(report)
    )
    assert module.validate_research_event_authority_update_latency_floor_report_digest(
        report,
    )
    payload = report.payload
    assert payload == (
        module.research_event_authority_update_latency_floor_report_payload(report)
    )
    assert payload["event_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_objects(payload)
    json.dumps(payload, sort_keys=True)


def test_latency_floor_rows_classify_pass_watch_and_block_deterministically() -> None:
    report = build_report(
        observation("pass", authority_update_latency_seconds=d("1200.000000")),
        observation("watch", authority_update_latency_seconds=d("600.000000")),
        observation("block", authority_update_latency_seconds=d("120.000000")),
    )

    assert report.status == "block"
    assert report.event_count == d("3.000000")
    assert report.pass_event_count == d("1.000000")
    assert report.watch_event_count == d("1.000000")
    assert report.block_event_count == d("1.000000")
    assert report.below_latency_floor_event_count == d("2.000000")
    assert report.minimum_authority_update_latency_seconds == d("120.000000")
    assert report.maximum_latency_floor_gap_seconds == d("780.000000")
    assert report.average_latency_floor_score == d("0.600000")
    assert report.reason_codes == (
        "authority_update_latency_floor_block",
        "authority_update_latency_floor_watch",
        "authority_update_latency_floor_pass",
    )

    assert tuple(row.event_digest for row in report.rows) == (
        digest("block-event"),
        digest("watch-event"),
        digest("pass-event"),
    )
    blocked, watched, passed = report.rows
    assert blocked.rank == d("1.000000")
    assert blocked.status == "block"
    assert blocked.authority_update_latency_seconds == d("120.000000")
    assert blocked.latency_floor_gap_seconds == d("780.000000")
    assert blocked.latency_floor_score == d("0.133333")
    assert blocked.reason_codes == ("authority_update_latency_floor_block",)
    assert watched.status == "watch"
    assert watched.latency_floor_gap_seconds == d("300.000000")
    assert watched.latency_floor_score == d("0.666667")
    assert watched.reason_codes == ("authority_update_latency_floor_watch",)
    assert passed.status == "pass"
    assert passed.latency_floor_gap_seconds == d("0.000000")
    assert passed.latency_floor_score == d("1.000000")
    assert passed.reason_codes == ("authority_update_latency_floor_pass",)


def test_payload_serialization_and_validation_reject_tampering() -> None:
    module = api()
    report = build_report(observation())
    payload = module.research_event_authority_update_latency_floor_report_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["rows"][0]["latency_floor_score"] == "1.000000"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert module.validate_research_event_authority_update_latency_floor_report_payload(
        payload,
    )
    assert_no_numeric_objects(payload)

    tampered_payload = dict(payload)
    tampered_payload["event_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_authority_update_latency_floor_report_payload(
            tampered_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["event_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_event_authority_update_latency_floor_report_payload(
            numeric_payload,
        )

    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_research_event_authority_update_latency_floor_report_payload(
            flag_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload["rows"] = [dict(payload["rows"][0])]
    unsafe_payload["rows"][0]["event_digest"] = "raw-" + _join_parts("mark", "et")
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_authority_update_latency_floor_report_payload(
            unsafe_payload,
        )


def test_public_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_AUTHORITY_UPDATE_LATENCY_FLOOR_REPORT_CONFIG_VERSION",
        "ResearchEventAuthorityUpdateLatencyFloorConfig",
        "ResearchEventAuthorityUpdateLatencyFloorObservation",
        "ResearchEventAuthorityUpdateLatencyFloorRow",
        "ResearchEventAuthorityUpdateLatencyFloorReport",
        "build_research_event_authority_update_latency_floor_report",
        "research_event_authority_update_latency_floor_report_digest",
        "research_event_authority_update_latency_floor_report_payload",
        "validate_research_event_authority_update_latency_floor_report_digest",
        "validate_research_event_authority_update_latency_floor_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchEventAuthorityUpdateLatencyFloorConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(
            module.ResearchEventAuthorityUpdateLatencyFloorObservation,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchEventAuthorityUpdateLatencyFloorRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchEventAuthorityUpdateLatencyFloorReport):
            pass

    with pytest.raises(ValueError, match="authority_update_latency_seconds"):
        observation(authority_update_latency_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")

    for item in (config(), *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(("_count", "_seconds", "_score", "_rank")):
                assert type(value) is Decimal


def test_validation_rejects_bad_types_inconsistent_thresholds_and_future_times() -> None:
    module = api()
    with pytest.raises(ValueError, match="watch_latency_floor_seconds"):
        config(watch_latency_floor_seconds=d("900.000000"))
    with pytest.raises(ValueError, match="pass_latency_floor_seconds"):
        config(pass_latency_floor_seconds=900)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_digest"):
        module.ResearchEventAuthorityUpdateLatencyFloorObservation(
            event_digest="not-a-digest",
            authority_digest=digest("authority"),
            observed_at=OBSERVED_AT,
            authority_update_latency_seconds=d("1.000000"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 11, 55))
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            observed_at=_DatetimeSubclass(2026, 7, 9, 11, 55, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_authority_update_latency_floor_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="authority_update_latency_seconds"):
        observation(authority_update_latency_seconds=d("-1.000000"))


def test_module_has_no_execution_or_unsafe_public_surfaces() -> None:
    module = api()
    public_names = set(module.__all__) | {
        name for name in dir(module) if not name.startswith("_")
    }
    for public_name in public_names:
        lower_name = public_name.lower()
        assert "db" not in lower_name
        for term in unsafe_terms():
            assert term not in lower_name

    source = inspect.getsource(module)
    for forbidden in (
        "requests",
        "urllib",
        "http.client",
        "socket",
        "sqlite",
        "sqlalchemy",
        "psycopg",
        "subprocess",
        "Path(",
        "open(",
        ".write(",
        ".read(",
        _join_parts("wal", "let"),
        _join_parts("ord", "er"),
        _join_parts("tra", "de"),
        _join_parts("li", "ve"),
        _join_parts("siz", "ing"),
        _join_parts("recomm", "endation"),
    ):
        assert forbidden not in source
