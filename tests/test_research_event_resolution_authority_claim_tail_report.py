from __future__ import annotations

import hashlib
import importlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone
from decimal import Decimal
from typing import Any

import pytest


MODULE_NAME = (
    "polymarket_alpha_lab."
    "research_event_resolution_authority_claim_tail_report"
)
GENERATED_AT = datetime(2026, 7, 9, 16, 45, tzinfo=UTC)


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


def payload_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest", None)
    encoded = json.dumps(
        digest_payload,
        sort_keys=True,
        separators=(",", ":"),
    ).encode("utf-8")
    return hashlib.sha256(encoded).hexdigest()


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def unsafe_terms() -> tuple[str, ...]:
    return (
        _join_parts("raw", "_id"),
        _join_parts("cand", "idate"),
        _join_parts("mark", "et"),
        _join_parts("sl", "ug"),
        _join_parts("que", "stion"),
        _join_parts("sour", "ce"),
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
        "://",
        "http",
        "www.",
    )


def config(**overrides: object) -> Any:
    module = api()
    values = {
        "pass_claim_age_seconds": d("3600.000000"),
        "watch_claim_age_seconds": d("14400.000000"),
        "pass_authority_delay_seconds": d("1800.000000"),
        "watch_authority_delay_seconds": d("7200.000000"),
        "min_pass_authority_confidence": d("0.800000"),
        "min_watch_authority_confidence": d("0.600000"),
        "max_pass_claim_conflict_pressure": d("0.100000"),
        "max_watch_claim_conflict_pressure": d("0.300000"),
        "min_pass_authority_quorum_ratio": d("1.000000"),
        "min_watch_authority_quorum_ratio": d("0.500000"),
    }
    values.update(overrides)
    return module.ResearchEventResolutionAuthorityClaimTailConfig(**values)


def observation(
    seed: str = "pass",
    *,
    claim_age_seconds: Decimal = d("900.000000"),
    authority_delay_seconds: Decimal = d("300.000000"),
    authority_confidence: Decimal = d("0.950000"),
    claim_conflict_pressure: Decimal = d("0.020000"),
    matched_authority_count: Decimal = d("2.000000"),
    required_authority_count: Decimal = d("2.000000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> Any:
    module = api()
    return module.ResearchEventResolutionAuthorityClaimTailObservation(
        private_event_ref=f"{seed}-event-private-ref",
        private_claim_ref=f"{seed}-claim-private-ref",
        private_authority_ref=f"{seed}-authority-private-ref",
        claim_age_seconds=claim_age_seconds,
        authority_delay_seconds=authority_delay_seconds,
        authority_confidence=authority_confidence,
        claim_conflict_pressure=claim_conflict_pressure,
        matched_authority_count=matched_authority_count,
        required_authority_count=required_authority_count,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def build_report(*items: Any, cfg: Any | None = None, generated_at: datetime = GENERATED_AT) -> Any:
    module = api()
    return module.build_research_event_resolution_authority_claim_tail_report(
        items,
        config=cfg if cfg is not None else config(),
        generated_at=generated_at,
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


def test_empty_report_is_pass_report_only_readonly_and_digest_validated() -> None:
    module = api()
    report = build_report()

    assert module.RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_STATUSES == (
        "pass",
        "watch",
        "block",
    )
    assert module.__all__ == (
        "DEFAULT_RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_CONFIG_VERSION",
        "RESEARCH_EVENT_RESOLUTION_AUTHORITY_CLAIM_TAIL_REPORT_STATUSES",
        "ResearchEventResolutionAuthorityClaimTailConfig",
        "ResearchEventResolutionAuthorityClaimTailObservation",
        "ResearchEventResolutionAuthorityClaimTailReasonCodeCount",
        "ResearchEventResolutionAuthorityClaimTailRow",
        "ResearchEventResolutionAuthorityClaimTailReport",
        "build_research_event_resolution_authority_claim_tail_report",
        "research_event_resolution_authority_claim_tail_report_digest",
        "research_event_resolution_authority_claim_tail_report_payload",
        "validate_research_event_resolution_authority_claim_tail_report_digest",
        "validate_research_event_resolution_authority_claim_tail_report_payload",
    )
    assert type(report) is module.ResearchEventResolutionAuthorityClaimTailReport
    assert is_dataclass(report)
    assert report.__dataclass_params__.frozen
    assert report.generated_at == GENERATED_AT
    assert report.status == "pass"
    assert report.claim_count == d("0.000000")
    assert report.pass_claim_count == d("0.000000")
    assert report.watch_claim_count == d("0.000000")
    assert report.block_claim_count == d("0.000000")
    assert report.tail_claim_count == d("0.000000")
    assert report.maximum_authority_claim_tail_score == d("0.000000")
    assert report.average_authority_claim_tail_score == d("0.000000")
    assert report.average_authority_confidence == d("0.000000")
    assert report.minimum_authority_quorum_ratio == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == (
        "research_event_resolution_authority_claim_tail_empty",
    )
    assert report.reason_code_counts == ()
    assert len(report.derived_validation_digest) == 64
    int(report.derived_validation_digest, 16)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert (
        report.derived_validation_digest
        == module.research_event_resolution_authority_claim_tail_report_digest(report)
    )
    assert module.validate_research_event_resolution_authority_claim_tail_report_digest(
        report,
    )
    assert report.payload == (
        module.research_event_resolution_authority_claim_tail_report_payload(report)
    )
    assert report.payload["claim_count"] == "0.000000"
    assert_no_numeric_objects(report.payload)
    json.dumps(report.payload, sort_keys=True)


def test_rows_classify_claim_tail_pass_watch_and_block_deterministically() -> None:
    passed = observation("pass")
    watched = observation(
        "watch",
        claim_age_seconds=d("7200.000000"),
        authority_delay_seconds=d("3600.000000"),
        authority_confidence=d("0.700000"),
        claim_conflict_pressure=d("0.200000"),
        matched_authority_count=d("1.000000"),
        required_authority_count=d("2.000000"),
    )
    blocked = observation(
        "block",
        claim_age_seconds=d("28800.000000"),
        authority_delay_seconds=d("14400.000000"),
        authority_confidence=d("0.400000"),
        claim_conflict_pressure=d("0.500000"),
        matched_authority_count=d("0.000000"),
        required_authority_count=d("2.000000"),
    )

    forward = build_report(passed, watched, blocked)
    reverse = build_report(blocked, watched, passed)

    assert forward == reverse
    assert forward.generated_at == GENERATED_AT
    assert forward.status == "block"
    assert forward.claim_count == d("3.000000")
    assert forward.pass_claim_count == d("1.000000")
    assert forward.watch_claim_count == d("1.000000")
    assert forward.block_claim_count == d("1.000000")
    assert forward.tail_claim_count == d("2.000000")
    assert forward.maximum_authority_claim_tail_score == d("0.820000")
    assert forward.average_authority_claim_tail_score == d("0.418278")
    assert forward.average_authority_confidence == d("0.683333")
    assert forward.minimum_authority_quorum_ratio == d("0.000000")
    assert forward.reason_codes == (
        "authority_claim_tail_block",
        "authority_claim_tail_watch",
        "authority_claim_tail_pass",
    )

    assert tuple(row.rank for row in forward.rows) == (
        d("1.000000"),
        d("2.000000"),
        d("3.000000"),
    )
    assert tuple(row.status for row in forward.rows) == ("block", "watch", "pass")
    blocked_row, watched_row, passed_row = forward.rows
    assert blocked_row.event_trace_hash == digest("block-event-private-ref")
    assert blocked_row.claim_trace_hash == digest("block-claim-private-ref")
    assert blocked_row.authority_trace_hash == digest("block-authority-private-ref")
    assert blocked_row.authority_quorum_ratio == d("0.000000")
    assert blocked_row.claim_age_tail_pressure == d("1.000000")
    assert blocked_row.authority_delay_tail_pressure == d("1.000000")
    assert blocked_row.confidence_gap_tail_pressure == d("0.600000")
    assert blocked_row.authority_quorum_tail_pressure == d("1.000000")
    assert blocked_row.authority_claim_tail_score == d("0.820000")
    assert blocked_row.reason_codes == (
        "authority_claim_tail_block",
        "claim_age_tail_block",
        "authority_delay_tail_block",
        "authority_confidence_tail_block",
        "claim_conflict_tail_block",
        "authority_quorum_tail_block",
    )
    assert watched_row.authority_quorum_ratio == d("0.500000")
    assert watched_row.authority_claim_tail_score == d("0.400000")
    assert watched_row.reason_codes == (
        "authority_claim_tail_watch",
        "claim_age_tail_watch",
        "authority_delay_tail_watch",
        "authority_confidence_tail_watch",
        "claim_conflict_tail_watch",
        "authority_quorum_tail_watch",
    )
    assert passed_row.authority_claim_tail_score == d("0.034833")
    assert passed_row.reason_codes == ("authority_claim_tail_pass",)

    counts = {item.reason_code: item for item in forward.reason_code_counts}
    assert counts["authority_claim_tail_block"] == (
        api().ResearchEventResolutionAuthorityClaimTailReasonCodeCount(
            reason_code="authority_claim_tail_block",
            count=d("1.000000"),
            input_ratio=d("0.333333"),
        )
    )


def test_payload_is_deterministic_public_safe_decimal_stringed_and_guarded() -> None:
    module = api()
    unsafe_private_value = (
        f"{_join_parts('raw', '_id')}:"
        f"{_join_parts('cand', 'idate')}:"
        f"{_join_parts('mark', 'et')}:"
        f"{_join_parts('sl', 'ug')}:"
        f"{_join_parts('que', 'stion')}:"
        f"{_join_parts('sour', 'ce')}_{_join_parts('ur', 'l')}:"
        f"{_join_parts('sour', 'ce')}_{_join_parts('te', 'xt')}:"
        f"{_join_parts('d', 'sn')}:"
        f"{_join_parts('ta', 'ble')}:"
        f"{_join_parts('to', 'ken')}:"
        f"{_join_parts('wal', 'let')}:"
        f"{_join_parts('ord', 'er')}:"
        f"{_join_parts('tra', 'de')}:"
        f"{_join_parts('siz', 'ing')}:"
        f"{_join_parts('recomm', 'endation')}:https://example.invalid/path"
    )
    unsafe_observation = module.ResearchEventResolutionAuthorityClaimTailObservation(
        private_event_ref=unsafe_private_value,
        private_claim_ref=f"{unsafe_private_value}-claim",
        private_authority_ref=f"{unsafe_private_value}-authority",
        claim_age_seconds=d("900.000000"),
        authority_delay_seconds=d("300.000000"),
        authority_confidence=d("0.950000"),
        claim_conflict_pressure=d("0.020000"),
        matched_authority_count=d("2.000000"),
        required_authority_count=d("2.000000"),
    )

    first = build_report(unsafe_observation, observation("alpha"))
    second = build_report(observation("alpha"), unsafe_observation)
    first_payload = (
        module.research_event_resolution_authority_claim_tail_report_payload(first)
    )
    second_payload = (
        module.research_event_resolution_authority_claim_tail_report_payload(second)
    )

    assert first == second
    assert first_payload == second_payload
    assert first_payload["derived_validation_digest"] == first.derived_validation_digest
    assert module.validate_research_event_resolution_authority_claim_tail_report_payload(
        first_payload,
    )
    assert (
        module.research_event_resolution_authority_claim_tail_report_digest(first)
        == module.research_event_resolution_authority_claim_tail_report_digest(second)
    )
    assert_no_numeric_objects(first_payload)
    encoded = json.dumps(first_payload, sort_keys=True).lower()
    for term in unsafe_terms():
        assert term not in encoded
    assert unsafe_private_value.lower() not in encoded

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(first, derived_validation_digest="0" * 64)

    tampered_payload = dict(first_payload)
    tampered_payload["claim_count"] = "99.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        module.validate_research_event_resolution_authority_claim_tail_report_payload(
            tampered_payload,
        )

    numeric_payload = dict(first_payload)
    numeric_payload["claim_count"] = 1
    with pytest.raises(ValueError, match="public payload"):
        module.validate_research_event_resolution_authority_claim_tail_report_payload(
            numeric_payload,
        )

    unsafe_payload = dict(first_payload)
    unsafe_payload[_join_parts("mark", "et_slug")] = "redacted"
    with pytest.raises(ValueError, match="unsafe public surface"):
        module.validate_research_event_resolution_authority_claim_tail_report_payload(
            unsafe_payload,
        )

    flag_payload = dict(first_payload)
    flag_payload["report_only"] = False
    with pytest.raises(ValueError, match="payload report_only must be True"):
        module.validate_research_event_resolution_authority_claim_tail_report_payload(
            flag_payload,
        )

    nested_flag_payload = json.loads(json.dumps(first_payload, sort_keys=True))
    nested_flag_payload["rows"][0]["paper_only"] = False
    nested_flag_payload["derived_validation_digest"] = payload_digest(
        nested_flag_payload,
    )
    with pytest.raises(ValueError, match="payload paper_only must be True"):
        module.validate_research_event_resolution_authority_claim_tail_report_payload(
            nested_flag_payload,
        )

    status_payload = json.loads(json.dumps(first_payload, sort_keys=True))
    status_payload["rows"][0]["status"] = "ready"
    status_payload["derived_validation_digest"] = payload_digest(status_payload)
    with pytest.raises(ValueError, match="payload status"):
        module.validate_research_event_resolution_authority_claim_tail_report_payload(
            status_payload,
        )


def test_public_dataclasses_are_frozen_decimal_only_and_reject_subclassing() -> None:
    module = api()
    for exported_name in module.__all__:
        value = getattr(module, exported_name)
        if isinstance(value, type):
            assert is_dataclass(value)
            assert value.__dataclass_params__.frozen

    report = build_report(observation())
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeConfig(module.ResearchEventResolutionAuthorityClaimTailConfig):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeObservation(
            module.ResearchEventResolutionAuthorityClaimTailObservation,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReasonCount(
            module.ResearchEventResolutionAuthorityClaimTailReasonCodeCount,
        ):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeRow(module.ResearchEventResolutionAuthorityClaimTailRow):
            pass

    with pytest.raises(TypeError, match="subclassing"):

        class UnsafeReport(module.ResearchEventResolutionAuthorityClaimTailReport):
            pass

    with pytest.raises(ValueError, match="claim_age_seconds"):
        observation(claim_age_seconds=_DecimalSubclass("1.000000"))
    with pytest.raises(ValueError, match="paper_only must be True"):
        observation(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(report, readonly=False)
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="ready")

    for item in (config(), *report.reason_code_counts, *report.rows, report):
        for field in fields(item):
            value = getattr(item, field.name)
            assert type(value) is not float
            if field.name.endswith(
                (
                    "_count",
                    "_ratio",
                    "_score",
                    "_seconds",
                    "_confidence",
                    "_pressure",
                    "_rank",
                ),
            ):
                assert type(value) is Decimal


def test_validation_rejects_bad_types_thresholds_counts_and_duplicates() -> None:
    module = api()
    with pytest.raises(ValueError, match="pass_claim_age_seconds"):
        config(pass_claim_age_seconds=d("14400.000000"))
    with pytest.raises(ValueError, match="pass_authority_delay_seconds"):
        config(pass_authority_delay_seconds=d("7200.000000"))
    with pytest.raises(ValueError, match="min_watch_authority_confidence"):
        config(min_watch_authority_confidence=d("0.800000"))
    with pytest.raises(ValueError, match="max_pass_claim_conflict_pressure"):
        config(max_pass_claim_conflict_pressure=d("0.300000"))
    with pytest.raises(ValueError, match="min_pass_authority_quorum_ratio"):
        config(min_pass_authority_quorum_ratio=1.0)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=datetime(2026, 7, 9, 16, 45))
    with pytest.raises(ValueError, match="generated_at"):
        build_report(generated_at=_DatetimeSubclass(2026, 7, 9, 16, 45, tzinfo=UTC))
    assert build_report(
        observation(),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    ).generated_at == GENERATED_AT
    with pytest.raises(ValueError, match="private_event_ref"):
        module.ResearchEventResolutionAuthorityClaimTailObservation(
            private_event_ref="",
            private_claim_ref="claim",
            private_authority_ref="authority",
            claim_age_seconds=d("1.000000"),
            authority_delay_seconds=d("1.000000"),
            authority_confidence=d("1.000000"),
            claim_conflict_pressure=d("0.000000"),
            matched_authority_count=d("1.000000"),
            required_authority_count=d("1.000000"),
        )
    with pytest.raises(ValueError, match="matched_authority_count"):
        observation(matched_authority_count=d("3.000000"))
    with pytest.raises(ValueError, match="required_authority_count"):
        observation(required_authority_count=d("0.000000"))
    with pytest.raises(ValueError, match="duplicate authority claim traces"):
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

    payload = build_report(observation("safe")).payload
    encoded = json.dumps(payload, sort_keys=True).lower()
    for term in unsafe_terms():
        assert term not in encoded

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
        _join_parts("raw", "_id"),
        _join_parts("cand", "idate"),
        _join_parts("mark", "et"),
        _join_parts("sl", "ug"),
        _join_parts("que", "stion"),
        _join_parts("sour", "ce"),
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
    ):
        assert forbidden not in source
