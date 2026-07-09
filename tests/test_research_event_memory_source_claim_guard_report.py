from __future__ import annotations

import hashlib
import inspect
import json
from dataclasses import FrozenInstanceError, fields, replace
from datetime import UTC, datetime, timedelta, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

import polymarket_alpha_lab.research_event_memory_source_claim_guard_report as api
from polymarket_alpha_lab.research_event_memory_source_claim_guard_report import (
    DEFAULT_RESEARCH_EVENT_MEMORY_SOURCE_CLAIM_GUARD_REPORT_CONFIG_VERSION,
    ResearchEventMemorySourceClaimGuardConfig,
    ResearchEventMemorySourceClaimGuardInputRow,
    ResearchEventMemorySourceClaimGuardPublicPayloadItem,
    ResearchEventMemorySourceClaimGuardReport,
    build_research_event_memory_source_claim_guard_report,
    research_event_memory_source_claim_guard_report_public_payload,
    validate_research_event_memory_source_claim_guard_report_public_payload,
)


NOW = datetime(2026, 7, 8, 12, 0, tzinfo=UTC)


class _DecimalSubclass(Decimal):
    pass


class _NaiveTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def _join_parts(*parts: str) -> str:
    return "".join(parts)


def _claim(
    event_memory_key: str,
    evidence_channel: str,
    claim_position: str,
    *,
    observed_at: datetime = NOW,
    credibility_weight_score: Decimal = d("0.900000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> ResearchEventMemorySourceClaimGuardInputRow:
    return ResearchEventMemorySourceClaimGuardInputRow(
        event_memory_key=event_memory_key,
        evidence_channel=evidence_channel,
        claim_position=claim_position,
        observed_at=observed_at,
        credibility_weight_score=credibility_weight_score,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def _config(**overrides: object) -> ResearchEventMemorySourceClaimGuardConfig:
    values = {
        "config_version": (
            DEFAULT_RESEARCH_EVENT_MEMORY_SOURCE_CLAIM_GUARD_REPORT_CONFIG_VERSION
        ),
        "min_claim_count": d("2.000000"),
        "min_independent_channel_count": d("2.000000"),
        "stale_claim_age_seconds": d("86400.000000"),
        "contradiction_watch_threshold": d("0.250000"),
        "contradiction_block_threshold": d("0.500000"),
        "credibility_watch_threshold": d("0.600000"),
        "credibility_block_threshold": d("0.300000"),
    }
    values.update(overrides)
    return ResearchEventMemorySourceClaimGuardConfig(**values)


def _sample_claims() -> tuple[ResearchEventMemorySourceClaimGuardInputRow, ...]:
    return (
        _claim("event_pass", "registry", "supports"),
        _claim("event_pass", "filing", "supports"),
        _claim("event_pass", "briefing", "supports"),
        _claim("event_watch", "registry", "supports"),
        _claim("event_watch", "filing", "supports"),
        _claim("event_watch", "briefing", "contradicts"),
        _claim("event_block", "registry", "supports", credibility_weight_score=d("0.400000")),
        _claim(
            "event_block",
            "filing",
            "contradicts",
            observed_at=NOW - timedelta(days=3),
            credibility_weight_score=d("0.400000"),
        ),
        _claim(
            "event_block",
            "briefing",
            "contradicts",
            observed_at=NOW - timedelta(days=2),
            credibility_weight_score=d("0.400000"),
        ),
    )


def _build_report(
    claims: tuple[ResearchEventMemorySourceClaimGuardInputRow, ...],
    *,
    public_payload: tuple[ResearchEventMemorySourceClaimGuardPublicPayloadItem, ...] = (),
) -> ResearchEventMemorySourceClaimGuardReport:
    return build_research_event_memory_source_claim_guard_report(
        claims,
        generated_at=NOW,
        config=_config(),
        public_payload=public_payload,
    )


def test_event_memory_claim_guard_flags_block_watch_and_sorts_deterministically() -> None:
    report = _build_report(tuple(reversed(_sample_claims())))

    assert report == ResearchEventMemorySourceClaimGuardReport(
        generated_at=NOW,
        config_version=(
            DEFAULT_RESEARCH_EVENT_MEMORY_SOURCE_CLAIM_GUARD_REPORT_CONFIG_VERSION
        ),
        guard_status="block",
        event_count=d("3.000000"),
        pass_count=d("1.000000"),
        watch_count=d("1.000000"),
        block_count=d("1.000000"),
        claim_count=d("9.000000"),
        contradiction_count=d("3.000000"),
        stale_claim_count=d("2.000000"),
        average_contradiction_ratio=d("0.333333"),
        average_credibility_weight_score=d("0.733333"),
        rows=report.rows,
        reason_codes=(
            "contradiction_pressure_watch",
            "contradiction_pressure_block",
            "stale_memory_claims",
            "claim_guard_pass",
        ),
        public_payload=(),
        derived_validation_digest=report.derived_validation_digest,
    )
    assert tuple(row.event_memory_key for row in report.rows) == (
        "event_block",
        "event_watch",
        "event_pass",
    )

    block_row = report.rows[0]
    assert block_row.guard_status == "block"
    assert block_row.claim_count == d("3.000000")
    assert block_row.independent_channel_count == d("3.000000")
    assert block_row.support_count == d("1.000000")
    assert block_row.contradiction_count == d("2.000000")
    assert block_row.contradiction_ratio == d("0.666667")
    assert block_row.stale_claim_count == d("2.000000")
    assert block_row.credibility_weight_score == d("0.400000")
    assert block_row.reason_codes == (
        "contradiction_pressure_block",
        "stale_memory_claims",
    )

    watch_row = report.rows[1]
    assert watch_row.guard_status == "watch"
    assert watch_row.contradiction_ratio == d("0.333333")
    assert watch_row.reason_codes == ("contradiction_pressure_watch",)

    pass_row = report.rows[2]
    assert pass_row.guard_status == "pass"
    assert pass_row.contradiction_ratio == d("0.000000")
    assert pass_row.reason_codes == ("claim_guard_pass",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True


def test_public_payload_is_deterministic_redacted_decimal_stringed_and_digest_checked() -> None:
    public_payload = (
        ResearchEventMemorySourceClaimGuardPublicPayloadItem(
            "summary_scope",
            "public rollup only",
        ),
    )
    report = _build_report(_sample_claims(), public_payload=public_payload)
    reversed_report = _build_report(
        tuple(reversed(_sample_claims())),
        public_payload=public_payload,
    )

    payload = research_event_memory_source_claim_guard_report_public_payload(report)
    reversed_payload = research_event_memory_source_claim_guard_report_public_payload(
        reversed_report,
    )

    json.dumps(payload, sort_keys=True)
    encoded_payload = json.dumps(payload, sort_keys=True)
    assert payload == reversed_payload
    assert payload["event_count"] == "3.000000"
    assert payload["claim_count"] == "9.000000"
    assert payload["average_contradiction_ratio"] == "0.333333"
    assert payload["generated_at"] == "2026-07-08T12:00:00+00:00"
    assert payload["rows"][0]["event_memory_key"] == "event_block"
    assert payload["rows"][0]["contradiction_ratio"] == "0.666667"
    assert payload["public_payload"] == [
        {
            "key": "summary_scope",
            "value": "public rollup only",
            "paper_only": True,
            "report_only": True,
            "readonly": True,
        },
    ]
    assert payload["derived_validation_digest"] == report.derived_validation_digest
    assert len(report.derived_validation_digest) == 64
    assert report.payload == payload
    assert validate_research_event_memory_source_claim_guard_report_public_payload(payload)
    assert report.derived_validation_digest == _digest_without_digest(payload)
    _assert_no_decimal_objects(payload)
    _assert_no_leaky_public_surface(encoded_payload)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(report, derived_validation_digest="0" * 64)

    with pytest.raises(ValueError, match="derived_validation_digest"):
        replace(
            report,
            public_payload=(
                ResearchEventMemorySourceClaimGuardPublicPayloadItem(
                    "summary_scope",
                    "changed rollup",
                ),
            ),
        )

    tampered = dict(payload)
    tampered["claim_count"] = "10.000000"
    with pytest.raises(ValueError, match="derived_validation_digest"):
        validate_research_event_memory_source_claim_guard_report_public_payload(tampered)


def test_frozen_dataclasses_reject_subclassing_and_keep_decimal_only_public_numbers() -> None:
    report = _build_report(_sample_claims())

    with pytest.raises(FrozenInstanceError):
        report.rows[0].guard_status = "watch"  # type: ignore[misc]

    with pytest.raises(TypeError):

        class BadConfig(ResearchEventMemorySourceClaimGuardConfig):
            pass

    for value in _walk_public_values(report):
        if isinstance(value, Decimal):
            assert type(value) is Decimal
        if type(value) is int or isinstance(value, float):
            raise AssertionError(f"public numeric value is not Decimal: {value!r}")

    for cls in (
        ResearchEventMemorySourceClaimGuardConfig,
        ResearchEventMemorySourceClaimGuardInputRow,
        type(report.rows[0]),
        ResearchEventMemorySourceClaimGuardPublicPayloadItem,
        ResearchEventMemorySourceClaimGuardReport,
    ):
        defaults = {field.name: field.default for field in fields(cls)}
        assert defaults["paper_only"] is True
        assert defaults["report_only"] is True
        assert defaults["readonly"] is True


def test_rejects_bad_flags_decimals_times_statuses_and_leaky_public_surfaces() -> None:
    with pytest.raises(ValueError, match="paper_only"):
        ResearchEventMemorySourceClaimGuardConfig(paper_only=False)
    with pytest.raises(ValueError, match="min_claim_count"):
        ResearchEventMemorySourceClaimGuardConfig(min_claim_count=2)
    with pytest.raises(ValueError, match="credibility_weight_score"):
        _claim("bad_weight", "registry", "supports", credibility_weight_score=1)
    with pytest.raises(ValueError, match="credibility_weight_score"):
        _claim(
            "bad_subclass",
            "registry",
            "supports",
            credibility_weight_score=_DecimalSubclass("1.000000"),
        )
    with pytest.raises(ValueError, match="claim_position"):
        _claim("bad_position", "registry", "maybe")
    with pytest.raises(ValueError, match="timezone-aware"):
        _claim("bad_time", "registry", "supports", observed_at=datetime(2026, 7, 8))
    with pytest.raises(ValueError, match="timezone-aware"):
        _claim(
            "bad_tz",
            "registry",
            "supports",
            observed_at=datetime(2026, 7, 8, tzinfo=_NaiveTz()),
        )
    with pytest.raises(ValueError, match="readonly"):
        _claim("bad_flag", "registry", "supports", readonly=False)
    with pytest.raises(ValueError, match="future"):
        build_research_event_memory_source_claim_guard_report(
            (_claim("future_claim", "registry", "supports", observed_at=NOW + timedelta(minutes=1)),),
            generated_at=NOW,
            config=_config(),
        )
    with pytest.raises(ValueError, match="event_memory_key"):
        _claim(_join_parts("candidate", "_", "abc"), "registry", "supports")
    with pytest.raises(ValueError, match="event_memory_key"):
        _claim(_join_parts("market", "_", "abc"), "registry", "supports")
    with pytest.raises(ValueError, match="evidence_channel"):
        _claim("safe_event", _join_parts("source", "_", "url"), "supports")
    with pytest.raises(ValueError, match="value"):
        ResearchEventMemorySourceClaimGuardPublicPayloadItem(
            "summary_scope",
            _join_parts("https", "://example.invalid/raw"),
        )
    with pytest.raises(ValueError, match="key"):
        ResearchEventMemorySourceClaimGuardPublicPayloadItem(
            _join_parts("dsn", "_", "label"),
            "public rollup only",
        )
    with pytest.raises(ValueError, match="payload"):
        validate_research_event_memory_source_claim_guard_report_public_payload(
            {"derived_validation_digest": "0" * 64, "raw": _join_parts("token")},
        )


def test_empty_input_returns_blocked_readonly_zeroed_report() -> None:
    report = build_research_event_memory_source_claim_guard_report(
        (),
        generated_at=NOW,
        config=_config(),
    )

    assert report.guard_status == "block"
    assert report.event_count == d("0.000000")
    assert report.claim_count == d("0.000000")
    assert report.rows == ()
    assert report.reason_codes == ("claim_guard_no_inputs",)
    assert report.paper_only is True
    assert report.report_only is True
    assert report.readonly is True
    assert report.payload["derived_validation_digest"] == report.derived_validation_digest


def test_module_surface_has_no_live_action_or_external_access_terms() -> None:
    source = inspect.getsource(api).lower()
    for forbidden in (
        "database",
        "network",
        "wallet",
        "order",
        "live trading",
        "sizing",
        "recommendation",
    ):
        assert forbidden not in source

    module_path = Path(api.__file__).read_text(encoding="utf-8")
    assert "requests" not in module_path
    assert "socket" not in module_path
    assert "psycopg" not in module_path
    assert "sqlalchemy" not in module_path


def _digest_without_digest(payload: dict[str, Any]) -> str:
    digest_payload = dict(payload)
    digest_payload.pop("derived_validation_digest")
    canonical = json.dumps(digest_payload, sort_keys=True, separators=(",", ":"))
    return hashlib.sha256(canonical.encode("utf-8")).hexdigest()


def _assert_no_decimal_objects(value: object) -> None:
    if isinstance(value, Decimal):
        raise AssertionError("payload should render Decimal values as strings")
    if isinstance(value, dict):
        for child in value.values():
            _assert_no_decimal_objects(child)
    elif isinstance(value, list):
        for child in value:
            _assert_no_decimal_objects(child)


def _assert_no_leaky_public_surface(encoded_payload: str) -> None:
    lowered = encoded_payload.lower()
    for forbidden in (
        "candidate",
        "market",
        "source_url",
        "source_text",
        "dsn",
        "table",
        "token",
        "http",
        "www",
    ):
        assert forbidden not in lowered


def _walk_public_values(value: object) -> tuple[object, ...]:
    seen: list[object] = []

    def walk(item: object) -> None:
        seen.append(item)
        if hasattr(item, "__dataclass_fields__"):
            for field in fields(item):
                walk(getattr(item, field.name))
        elif isinstance(item, tuple):
            for child in item:
                walk(child)

    walk(value)
    return tuple(seen)
