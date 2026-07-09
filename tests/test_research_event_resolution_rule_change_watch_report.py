from __future__ import annotations

from dataclasses import FrozenInstanceError, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from importlib import import_module
import json
from pathlib import Path
from typing import Any

import pytest


GENERATED_AT = datetime(2026, 7, 9, 12, 0, tzinfo=UTC)
RECENT_AT = datetime(2026, 7, 9, 11, 45, tzinfo=UTC)
STALE_AT = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
ONE = Decimal("1.000000")
MODULE_PATH = (
    Path(__file__).resolve().parents[1]
    / "src"
    / "polymarket_alpha_lab"
    / "research_event_resolution_rule_change_watch_report.py"
)


class _DecimalSubclass(Decimal):
    pass


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def _api():
    return import_module(
        "polymarket_alpha_lab.research_event_resolution_rule_change_watch_report",
    )


def d(value: str) -> Decimal:
    return Decimal(value)


def _config(**overrides: object):
    api = _api()
    values = {
        "config_version": (
            api.DEFAULT_RESEARCH_EVENT_RESOLUTION_RULE_CHANGE_WATCH_REPORT_CONFIG_VERSION
        ),
        "watch_rule_change_score": d("0.250000"),
        "block_rule_change_score": d("0.600000"),
        "watch_authority_update_score": d("0.250000"),
        "block_authority_update_score": d("0.600000"),
        "watch_clause_change_score": d("0.250000"),
        "block_clause_change_score": d("0.600000"),
        "watch_authority_gap_count": d("1.000000"),
        "block_authority_gap_count": d("2.000000"),
        "max_unreviewed_change_age_seconds": d("86400.000000"),
    }
    values.update(overrides)
    return api.ResearchEventResolutionRuleChangeWatchConfig(**values)


def _candidate(
    event_key: str = "event-alpha",
    *,
    rule_change_score: Decimal = d("0.000000"),
    authority_update_score: Decimal = d("0.000000"),
    clause_change_score: Decimal = d("0.000000"),
    authority_gap_count: Decimal = d("0.000000"),
    rule_checked_at: datetime = RECENT_AT,
    review_completed: bool = True,
):
    api = _api()
    return api.ResearchEventResolutionRuleChangeWatchInput(
        event_key=event_key,
        rule_change_score=rule_change_score,
        authority_update_score=authority_update_score,
        clause_change_score=clause_change_score,
        authority_gap_count=authority_gap_count,
        rule_checked_at=rule_checked_at,
        review_completed=review_completed,
    )


def _report(rows: tuple[object, ...], *, cfg=None, generated_at: datetime = GENERATED_AT):
    api = _api()
    return api.build_research_event_resolution_rule_change_watch_report(
        rows,
        config=cfg or _config(),
        generated_at=generated_at,
    )


def test_rule_change_watch_classifies_pass_watch_and_block_rows() -> None:
    api = _api()
    report = _report(
        (
            _candidate(
                "event-block",
                rule_change_score=d("0.650000"),
                authority_update_score=d("0.700000"),
                clause_change_score=d("0.620000"),
                authority_gap_count=d("2.000000"),
                rule_checked_at=STALE_AT,
                review_completed=False,
            ),
            _candidate(
                "event-watch",
                clause_change_score=d("0.300000"),
                authority_gap_count=d("1.000000"),
                rule_checked_at=GENERATED_AT - timedelta(minutes=15),
                review_completed=True,
            ),
            _candidate(
                "event-pass",
                rule_checked_at=GENERATED_AT - timedelta(minutes=5),
                review_completed=True,
            ),
        ),
        generated_at=datetime(2026, 7, 9, 8, 0, tzinfo=timezone(timedelta(hours=-4))),
    )

    assert type(report) is api.ResearchEventResolutionRuleChangeWatchReport
    assert is_dataclass(report)
    assert report.generated_at == GENERATED_AT
    assert report.observed_event_count == d("3.000000")
    assert report.pass_event_count == d("1.000000")
    assert report.watch_event_count == d("1.000000")
    assert report.block_event_count == d("1.000000")
    assert report.changed_event_count == d("2.000000")
    assert report.review_required_count == d("2.000000")
    assert report.missing_review_count == d("1.000000")
    assert report.max_rule_change_score == d("0.650000")
    assert report.max_authority_update_score == d("0.700000")
    assert report.max_clause_change_score == d("0.620000")
    assert report.max_change_score == d("0.700000")
    assert report.max_change_age_seconds == d("86400.000000")
    assert report.watch_ratio == d("0.666667")
    assert report.block_ratio == d("0.333333")
    assert report.status == "block"
    assert report.reason_codes == (
        "rule_change_present",
        "authority_update_present",
        "clause_change_present",
        "authority_gap_present",
        "resolution_rule_review_required_present",
        "missing_resolution_rule_review_present",
        "resolution_rule_change_block_present",
    )
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True

    block_row, watch_row, pass_row = report.rows
    assert block_row == api.ResearchEventResolutionRuleChangeWatchRow(
        event_key="event-block",
        status="block",
        rule_change_score=d("0.650000"),
        authority_update_score=d("0.700000"),
        clause_change_score=d("0.620000"),
        authority_gap_count=d("2.000000"),
        max_change_score=d("0.700000"),
        change_age_seconds=d("86400.000000"),
        rule_change_detected=True,
        authority_update_detected=True,
        clause_change_detected=True,
        authority_gap_detected=True,
        review_required=True,
        missing_review=True,
        reason_codes=(
            "rule_change_block",
            "authority_update_block",
            "clause_change_block",
            "authority_gap_block",
            "resolution_rule_review_required",
            "missing_resolution_rule_review_block",
        ),
    )
    assert watch_row.event_key == "event-watch"
    assert watch_row.status == "watch"
    assert watch_row.reason_codes == (
        "clause_change_watch",
        "authority_gap_watch",
        "resolution_rule_review_required",
    )
    assert pass_row.event_key == "event-pass"
    assert pass_row.status == "pass"
    assert pass_row.reason_codes == ("resolution_rule_change_clear",)


def test_stale_missing_review_escalates_watch_level_change_to_block() -> None:
    report = _report(
        (
            _candidate(
                "event-stale-watch",
                rule_change_score=d("0.300000"),
                rule_checked_at=STALE_AT,
                review_completed=False,
            ),
        ),
    )

    (row,) = report.rows
    assert row.status == "block"
    assert row.reason_codes == (
        "rule_change_watch",
        "resolution_rule_review_required",
        "missing_resolution_rule_review_block",
    )
    assert report.block_event_count == ONE
    assert report.watch_event_count == ZERO


def test_empty_and_clear_reports_are_pass_decimal_json_ready_and_digest_validated() -> None:
    api = _api()
    empty = _report(())
    clear = _report((_candidate("event-clear"),))

    assert empty.observed_event_count == ZERO
    assert empty.watch_ratio == ZERO
    assert empty.block_ratio == ZERO
    assert empty.status == "pass"
    assert empty.reason_codes == ("resolution_rule_change_watch_clear",)
    assert empty.rows == ()

    payload = api.research_event_resolution_rule_change_watch_report_payload(clear)
    repeat_payload = api.research_event_resolution_rule_change_watch_report_payload(clear)

    assert clear.observed_event_count == ONE
    assert clear.pass_event_count == ONE
    assert clear.status == "pass"
    assert clear.reason_codes == ("resolution_rule_change_watch_clear",)
    assert payload == repeat_payload
    assert payload["generated_at"] == GENERATED_AT.isoformat()
    assert payload["observed_event_count"] == "1.000000"
    assert payload["watch_ratio"] == "0.000000"
    assert payload["rows"][0]["event_key"] == "event-clear"
    assert payload["rows"][0]["max_change_score"] == "0.000000"
    assert payload["derived_validation_digest"] == clear.derived_validation_digest
    assert len(clear.derived_validation_digest) == 64
    assert int(clear.derived_validation_digest, 16) >= 0
    assert json.dumps(payload, sort_keys=True) == json.dumps(repeat_payload, sort_keys=True)
    assert api.validate_research_event_resolution_rule_change_watch_report_payload(payload)
    assert api.research_event_resolution_rule_change_watch_report_payload(payload) == payload
    assert not _contains_float_or_int(payload)
    assert not _has_forbidden_public_key(payload)

    reordered_payload = {
        key: payload[key]
        for key in reversed(tuple(payload.keys()))
    }
    with pytest.raises(ValueError, match="public readonly schema"):
        api.research_event_resolution_rule_change_watch_report_payload(reordered_payload)

    reordered_row = {
        key: payload["rows"][0][key]
        for key in reversed(tuple(payload["rows"][0].keys()))
    }
    with pytest.raises(ValueError, match="public readonly schema"):
        api.research_event_resolution_rule_change_watch_report_payload(
            {**payload, "rows": [reordered_row]},
        )


def test_payload_rejects_sensitive_keys_values_flags_and_digest_downgrades() -> None:
    api = _api()
    report = _report(
        (
            _candidate(
                clause_change_score=d("0.300000"),
                authority_gap_count=d("1.000000"),
            ),
        ),
    )
    payload = api.research_event_resolution_rule_change_watch_report_payload(report)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)
    with pytest.raises(ValueError, match="derived_validation_digest"):
        api.validate_research_event_resolution_rule_change_watch_report_payload(
            {**payload, "status": "pass"},
        )
    with pytest.raises(ValueError, match="paper_only"):
        api.research_event_resolution_rule_change_watch_report_payload(
            {**payload, "paper_only": False},
        )
    with pytest.raises(ValueError, match="Decimal-derived"):
        api.research_event_resolution_rule_change_watch_report_payload(
            {**payload, "observed_event_count": 1},
        )
    with pytest.raises(ValueError, match="float"):
        api.research_event_resolution_rule_change_watch_report_payload(
            {**payload, "watch_ratio": 0.5},
        )

    unsafe_keys = (
        "raw_" + "candidate_id",
        "market_" + "id",
        "market_" + "slug",
        "ques" + "tion",
        "source_" + "url",
        "source_" + "text",
        "dsn",
        "table" + "_name",
        "auth_" + "token",
        "wallet_" + "address",
        "order_" + "id",
        "trade_" + "id",
    )
    for unsafe_key in unsafe_keys:
        with pytest.raises(ValueError, match="unsafe"):
            api.research_event_resolution_rule_change_watch_report_payload(
                {**payload, unsafe_key: "redacted"},
            )

    unsafe_values = (
        "candidate_id=abc",
        "will-this-event-slug-leak",
        "https://example.invalid/rule",
        "source text copied from authority",
        "postgres://example",
        "token=secret",
        "wallet-address",
        "order-id",
        "trade-id",
    )
    for unsafe_value in unsafe_values:
        bad_row = {**payload["rows"][0], "event_key": unsafe_value}
        with pytest.raises(ValueError, match="unsafe|redacted public identifier"):
            api.research_event_resolution_rule_change_watch_report_payload(
                {**payload, "rows": [bad_row]},
            )

    serialized = repr(payload).lower()
    for banned in ("candidate_id", "market_id", "market_slug", "source_url", "token"):
        assert banned not in serialized


def test_dataclasses_are_frozen_strict_decimal_utc_and_source_has_no_live_surfaces() -> None:
    api = _api()
    report = _report((_candidate(),))

    public_classes = (
        api.ResearchEventResolutionRuleChangeWatchConfig,
        api.ResearchEventResolutionRuleChangeWatchInput,
        api.ResearchEventResolutionRuleChangeWatchRow,
        api.ResearchEventResolutionRuleChangeWatchReport,
    )
    assert all(is_dataclass(public_class) for public_class in public_classes)
    assert all(public_class.__dataclass_params__.frozen is True for public_class in public_classes)
    for public_class in public_classes:
        for field in fields(public_class):
            if field.name.endswith(("_count", "_score", "_ratio", "_seconds")):
                assert field.type in (Decimal, "Decimal")

    with pytest.raises(FrozenInstanceError):
        report.status = "watch"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        report.rows[0].status = "watch"  # type: ignore[misc]
    with pytest.raises(ValueError, match="paper_only"):
        replace(_config(), paper_only=False)
    with pytest.raises(ValueError, match="Decimal"):
        _config(watch_rule_change_score=_DecimalSubclass("0.250000"))
    with pytest.raises(ValueError, match="Decimal"):
        _candidate(rule_change_score=0.1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="Decimal"):
        _candidate(authority_gap_count=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="timezone-aware"):
        _candidate(rule_checked_at=datetime(2026, 7, 9, 11, 0))
    with pytest.raises(ValueError, match="timezone-aware"):
        _report((), generated_at=datetime(2026, 7, 9, 12, 0))
    with pytest.raises(ValueError, match="UTC offset"):
        _candidate(
            rule_checked_at=datetime(
                2026,
                7,
                9,
                11,
                0,
                tzinfo=_NoneOffsetTimezone(),
            ),
        )
    with pytest.raises(ValueError, match="after generated_at"):
        _report(
            (_candidate(rule_checked_at=GENERATED_AT + timedelta(seconds=1)),),
        )
    with pytest.raises(ValueError, match="event_key"):
        _candidate(event_key="event slug leak")
    with pytest.raises(ValueError, match="review_completed"):
        _candidate(review_completed=1)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="status"):
        replace(report.rows[0], status="watch")
    with pytest.raises(ValueError, match="pass_event_count"):
        replace(report, pass_event_count=ZERO)

    source = MODULE_PATH.read_text(encoding="utf-8").lower()
    forbidden_terms = (
        "requests",
        "urllib",
        "httpx",
        "aiohttp",
        "socket",
        "subprocess",
        "open(",
        "connect(",
        "raw_" + "candidate",
        "market_" + "id",
        "market_" + "slug",
        "source_" + "url",
        "source_" + "text",
        "wallet",
        "order",
        "trade",
    )
    assert all(term not in source for term in forbidden_terms)


def _contains_float_or_int(value: object) -> bool:
    if isinstance(value, dict):
        return any(_contains_float_or_int(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_float_or_int(item) for item in value)
    return type(value) in (float, int)


def _has_forbidden_public_key(value: object) -> bool:
    forbidden = (
        "raw_" + "candidate_id",
        "market_" + "id",
        "market_" + "slug",
        "ques" + "tion",
        "source_" + "url",
        "source_" + "text",
        "dsn",
        "table" + "_name",
        "token",
        "wallet",
        "order",
        "trade",
    )
    if isinstance(value, dict):
        for key, item in value.items():
            if any(term in str(key).lower() for term in forbidden):
                return True
            if _has_forbidden_public_key(item):
                return True
    if isinstance(value, list):
        return any(_has_forbidden_public_key(item) for item in value)
    return False
