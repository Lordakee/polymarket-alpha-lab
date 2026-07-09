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
    "research_event_resolution_source_latency_tail_report"
)
GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
OBSERVED_AT = datetime(2026, 7, 9, 11, 50, tzinfo=UTC)


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


def recompute_payload_digest(payload: dict[str, Any]) -> dict[str, Any]:
    signed = json.loads(json.dumps(payload, sort_keys=True))
    signed.pop("derived_validation_digest", None)
    signed["derived_validation_digest"] = hashlib.sha256(
        json.dumps(signed, sort_keys=True, separators=(",", ":")).encode("utf-8"),
    ).hexdigest()
    return signed


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "pass_latency_ceiling_seconds": d("600.000000"),
        "block_latency_ceiling_seconds": d("1800.000000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionSourceLatencyTailConfig(**values)


def observation(
    seed: str = "alpha",
    *,
    observed_at: datetime = OBSERVED_AT,
    resolution_source_latency_seconds: Decimal = d("300.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventResolutionSourceLatencyTailObservation(
        event_digest=digest(f"{seed}-event"),
        resolution_source_digest=digest(f"{seed}-resolution-source"),
        observed_at=observed_at,
        resolution_source_latency_seconds=resolution_source_latency_seconds,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None) -> Any:
    module = api()
    return module.build_research_event_resolution_source_latency_tail_report(
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
    assert type(value) not in (Decimal, float, int)


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
        _join_parts("au", "th"),
        _join_parts("exec", "ution"),
    )


def test_empty_report_is_pass_readonly_digest_validated_and_decimal_only() -> None:
    module = api()
    report = build_report()

    assert type(report) is module.ResearchEventResolutionSourceLatencyTailReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.event_count == d("0.000000")
    assert report.pass_event_count == d("0.000000")
    assert report.watch_event_count == d("0.000000")
    assert report.block_event_count == d("0.000000")
    assert report.tail_latency_event_count == d("0.000000")
    assert report.maximum_resolution_source_latency_seconds == d("0.000000")
    assert report.maximum_tail_excess_seconds == d("0.000000")
    assert report.average_tail_latency_score == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_event_resolution_source_latency_tail_empty",
    )
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert (
        report.derived_validation_digest
        == module.research_event_resolution_source_latency_tail_report_digest(report)
    )
    assert module.validate_research_event_resolution_source_latency_tail_report_digest(
        report,
    )
    payload = report.payload
    assert payload == (
        module.research_event_resolution_source_latency_tail_report_payload(report)
    )
    assert payload["event_count"] == "0.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert_no_numeric_objects(payload)
    json.dumps(payload, sort_keys=True)


def test_tail_rows_classify_pass_watch_and_block_deterministically() -> None:
    pass_item = observation(
        "pass",
        resolution_source_latency_seconds=d("300.000000"),
    )
    watch_item = observation(
        "watch",
        resolution_source_latency_seconds=d("1200.000000"),
    )
    block_item = observation(
        "block",
        resolution_source_latency_seconds=d("2400.000000"),
    )

    forward = build_report(pass_item, watch_item, block_item)
    reverse = build_report(block_item, watch_item, pass_item)

    assert forward == reverse
    assert forward.status == "block"
    assert forward.event_count == d("3.000000")
    assert forward.pass_event_count == d("1.000000")
    assert forward.watch_event_count == d("1.000000")
    assert forward.block_event_count == d("1.000000")
    assert forward.tail_latency_event_count == d("2.000000")
    assert forward.maximum_resolution_source_latency_seconds == d("2400.000000")
    assert forward.maximum_tail_excess_seconds == d("1800.000000")
    assert forward.average_tail_latency_score == d("0.611111")
    assert forward.reason_codes == (
        "resolution_source_latency_tail_block",
        "resolution_source_latency_tail_watch",
        "resolution_source_latency_tail_pass",
    )

    assert tuple(row.event_digest for row in forward.rows) == (
        digest("block-event"),
        digest("watch-event"),
        digest("pass-event"),
    )
    blocked, watched, passed = forward.rows
    assert blocked.rank == d("1.000000")
    assert blocked.status == "block"
    assert blocked.resolution_source_latency_seconds == d("2400.000000")
    assert blocked.tail_excess_seconds == d("1800.000000")
    assert blocked.tail_latency_score == d("1.000000")
    assert blocked.reason_codes == ("resolution_source_latency_tail_block",)
    assert watched.status == "watch"
    assert watched.tail_excess_seconds == d("600.000000")
    assert watched.tail_latency_score == d("0.666667")
    assert watched.reason_codes == ("resolution_source_latency_tail_watch",)
    assert passed.status == "pass"
    assert passed.tail_excess_seconds == d("0.000000")
    assert passed.tail_latency_score == d("0.166667")
    assert passed.reason_codes == ("resolution_source_latency_tail_pass",)


def test_payload_serialization_and_validation_reject_tampering() -> None:
    module = api()
    report = build_report(observation())
    payload = module.research_event_resolution_source_latency_tail_report_payload(
        report,
    )

    assert payload["generated_at"] == "2026-07-09T12:00:00+00:00"
    assert payload["event_count"] == "1.000000"
    assert payload["rows"][0]["tail_latency_score"] == "0.166667"
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert module.validate_research_event_resolution_source_latency_tail_report_payload(
        payload,
    )
    assert_no_numeric_objects(payload)

    tampered_payload = dict(payload)
    tampered_payload["event_count"] = "2.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_resolution_source_latency_tail_report_payload(
            tampered_payload,
        )

    numeric_payload = dict(payload)
    numeric_payload["event_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_event_resolution_source_latency_tail_report_payload(
            numeric_payload,
        )

    flag_payload = dict(payload)
    flag_payload["readonly"] = False
    with pytest.raises(ValueError, match="payload readonly must be True"):
        module.validate_research_event_resolution_source_latency_tail_report_payload(
            flag_payload,
        )

    unsafe_payload = dict(payload)
    unsafe_payload[_join_parts("mark", "et_slug")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_resolution_source_latency_tail_report_payload(
            unsafe_payload,
        )


def test_payload_validation_rejects_recomputed_digest_status_mutation() -> None:
    module = api()
    payload = module.research_event_resolution_source_latency_tail_report_payload(
        build_report(observation()),
    )
    mutated_payload = json.loads(json.dumps(payload, sort_keys=True))
    mutated_payload["status"] = "hold"
    mutated_payload["rows"][0]["status"] = "hold"

    with pytest.raises(ValueError, match="status"):
        module.validate_research_event_resolution_source_latency_tail_report_payload(
            recompute_payload_digest(mutated_payload),
        )


def test_payload_validation_rejects_recomputed_digest_unknown_public_keys() -> None:
    module = api()
    payload = module.research_event_resolution_source_latency_tail_report_payload(
        build_report(observation()),
    )
    mutated_payload = json.loads(json.dumps(payload, sort_keys=True))
    mutated_payload["annotation"] = "redacted"

    with pytest.raises(ValueError, match="canonical keys"):
        module.validate_research_event_resolution_source_latency_tail_report_payload(
            recompute_payload_digest(mutated_payload),
        )


def test_payload_validation_rejects_recomputed_digest_auth_and_execution_keys() -> None:
    module = api()
    payload = module.research_event_resolution_source_latency_tail_report_payload(
        build_report(observation()),
    )
    for unsafe_key in (
        _join_parts("au", "th_channel"),
        _join_parts("exec", "ution_surface"),
    ):
        mutated_payload = json.loads(json.dumps(payload, sort_keys=True))
        mutated_payload[unsafe_key] = "redacted"

        with pytest.raises(ValueError, match="unsafe public surface"):
            module.validate_research_event_resolution_source_latency_tail_report_payload(
                recompute_payload_digest(mutated_payload),
            )


def test_report_rejects_unsupported_config_version_before_digest_validation() -> None:
    report = build_report(observation())

    with pytest.raises(ValueError, match="config_version"):
        replace(report, config_version="unsupported")


def test_public_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    module = api()
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_SOURCE_LATENCY_TAIL_REPORT_CONFIG_VERSION",
        "ResearchEventResolutionSourceLatencyTailConfig",
        "ResearchEventResolutionSourceLatencyTailObservation",
        "ResearchEventResolutionSourceLatencyTailRow",
        "ResearchEventResolutionSourceLatencyTailReport",
        "build_research_event_resolution_source_latency_tail_report",
        "research_event_resolution_source_latency_tail_report_digest",
        "research_event_resolution_source_latency_tail_report_payload",
        "validate_research_event_resolution_source_latency_tail_report_digest",
        "validate_research_event_resolution_source_latency_tail_report_payload",
    )
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchEventResolutionSourceLatencyTailConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(
            module.ResearchEventResolutionSourceLatencyTailObservation,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchEventResolutionSourceLatencyTailRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchEventResolutionSourceLatencyTailReport):
            pass

    with pytest.raises(ValueError, match="resolution_source_latency_seconds"):
        observation(resolution_source_latency_seconds=_DecimalSubclass("1.000000"))
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


def test_validation_rejects_bad_types_thresholds_future_times_and_duplicates() -> None:
    module = api()
    with pytest.raises(ValueError, match="block_latency_ceiling_seconds"):
        config(block_latency_ceiling_seconds=d("600.000000"))
    with pytest.raises(ValueError, match="pass_latency_ceiling_seconds"):
        config(pass_latency_ceiling_seconds=600)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="event_digest"):
        module.ResearchEventResolutionSourceLatencyTailObservation(
            event_digest="not-a-digest",
            resolution_source_digest=digest("resolution-source"),
            observed_at=OBSERVED_AT,
            resolution_source_latency_seconds=d("1.000000"),
        )
    with pytest.raises(ValueError, match="observed_at"):
        observation(observed_at=datetime(2026, 7, 9, 11, 50))
    with pytest.raises(ValueError, match="observed_at"):
        observation(
            observed_at=_DatetimeSubclass(2026, 7, 9, 11, 50, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="generated_at"):
        module.build_research_event_resolution_source_latency_tail_report(
            (),
            config=config(),
            generated_at=datetime(2026, 7, 9, 12, 0),
        )
    with pytest.raises(ValueError, match="observed_at"):
        build_report(observation(observed_at=GENERATED_AT + timedelta(seconds=1)))
    with pytest.raises(ValueError, match="resolution_source_latency_seconds"):
        observation(resolution_source_latency_seconds=d("-1.000000"))
    with pytest.raises(ValueError, match="duplicate digests"):
        build_report(observation("dupe"), observation("dupe"))


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
