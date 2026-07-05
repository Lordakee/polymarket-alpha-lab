from __future__ import annotations

import ast
import importlib
import json
from dataclasses import FrozenInstanceError, asdict, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path
from typing import Any

import pytest

from polymarket_alpha_lab.market_research_policy_hearing_schedule_digest import (
    DEFAULT_MARKET_RESEARCH_POLICY_HEARING_SCHEDULE_DIGEST_CONFIG_VERSION,
    MarketResearchPolicyHearingScheduleDigestConfig,
    MarketResearchPolicyHearingScheduleDigestInputRow,
    MarketResearchPolicyHearingScheduleDigestReasonCodeCount,
    MarketResearchPolicyHearingScheduleDigestReport,
    MarketResearchPolicyHearingScheduleDigestRow,
    build_market_research_policy_hearing_schedule_digest,
    market_research_policy_hearing_schedule_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 4, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")
_UNSET = object()
MODULE_PATH = Path(
    "src/polymarket_alpha_lab/market_research_policy_hearing_schedule_digest.py",
)
PUBLIC_DATACLASSES = (
    MarketResearchPolicyHearingScheduleDigestConfig,
    MarketResearchPolicyHearingScheduleDigestInputRow,
    MarketResearchPolicyHearingScheduleDigestRow,
    MarketResearchPolicyHearingScheduleDigestReasonCodeCount,
    MarketResearchPolicyHearingScheduleDigestReport,
)


class _DateTimeSubclass(datetime):
    pass


class _NoneOffsetTz(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


def d(value: str) -> Decimal:
    return Decimal(value)


def config(**overrides: object) -> MarketResearchPolicyHearingScheduleDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_POLICY_HEARING_SCHEDULE_DIGEST_CONFIG_VERSION
        ),
        "fresh_schedule_max_age_seconds": d("86400.000000"),
        "min_public_source_count": d("2"),
        "near_hearing_window_seconds": d("172800.000000"),
        "stale_confirmation_after_seconds": d("21600.000000"),
        "min_cross_source_agreement": d("0.600000"),
        "materiality_watch_threshold": d("0.150000"),
        "materiality_block_threshold": d("0.350000"),
    }
    values.update(overrides)
    return MarketResearchPolicyHearingScheduleDigestConfig(**values)


def input_row(
    research_key: str = "research.policy.hearing.energy",
    *,
    condition_id: str = "condition_policy_hearing_energy",
    policy_area: str = "energy_permitting",
    hearing_id: str = "hearing_energy_permitting",
    public_schedule_reference: str = "public-hearing-notice",
    hearing_scheduled_at: datetime | None = None,
    schedule_observed_at: datetime | None = None,
    confirmed_at: object = _UNSET,
    public_source_count: Decimal = d("3"),
    cross_source_agreement: Decimal = d("0.800000"),
    schedule_materiality_score: Decimal = d("0.120000"),
    market_probability_before: Decimal = d("0.420000"),
    market_probability_after: Decimal = d("0.500000"),
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchPolicyHearingScheduleDigestInputRow:
    return MarketResearchPolicyHearingScheduleDigestInputRow(
        research_key=research_key,
        condition_id=condition_id,
        policy_area=policy_area,
        hearing_id=hearing_id,
        public_schedule_reference=public_schedule_reference,
        hearing_scheduled_at=hearing_scheduled_at or GENERATED_AT + timedelta(days=7),
        schedule_observed_at=schedule_observed_at or GENERATED_AT - timedelta(hours=1),
        confirmed_at=(
            GENERATED_AT - timedelta(minutes=30)
            if confirmed_at is _UNSET
            else confirmed_at
        ),
        public_source_count=public_source_count,
        cross_source_agreement=cross_source_agreement,
        schedule_materiality_score=schedule_materiality_score,
        market_probability_before=market_probability_before,
        market_probability_after=market_probability_after,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    rows: tuple[object, ...],
    *,
    cfg: MarketResearchPolicyHearingScheduleDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchPolicyHearingScheduleDigestReport:
    return build_market_research_policy_hearing_schedule_digest(
        rows,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def walk_values(value: Any) -> tuple[Any, ...]:
    if isinstance(value, dict):
        nested: list[Any] = []
        for item in value.values():
            nested.extend(walk_values(item))
        return tuple(nested)
    if isinstance(value, list):
        nested = []
        for item in value:
            nested.extend(walk_values(item))
        return tuple(nested)
    return (value,)


def assert_decimal_numeric_fields(value: object) -> None:
    for field in fields(value):
        if field.name in {"paper_only", "report_only", "readonly"}:
            continue
        item = getattr(value, field.name)
        if isinstance(item, Decimal) or item is None:
            continue
        if field.name.endswith("_count") or field.name.endswith("_ratio"):
            assert type(item) is Decimal
        if field.name.endswith("_seconds") or field.name.endswith("_score"):
            assert type(item) is Decimal
        if field.name.endswith("_change"):
            assert type(item) is Decimal


def test_policy_hearing_schedule_digest_reduces_redacts_and_sorts() -> None:
    summary = report(
        (
            input_row(
                "research.policy.hearing.archived",
                condition_id="condition_policy_hearing_archived",
                policy_area="archived_tax_rules",
                hearing_id="hearing_archived_tax_rules",
                public_schedule_reference="https://calendar.example/hearing?token=hidden",
                hearing_scheduled_at=GENERATED_AT - timedelta(hours=3),
                schedule_observed_at=GENERATED_AT - timedelta(hours=30),
                confirmed_at=GENERATED_AT - timedelta(hours=7),
                public_source_count=d("1"),
                cross_source_agreement=d("0.500000"),
                schedule_materiality_score=d("0.200000"),
                market_probability_before=d("0.300000"),
                market_probability_after=d("0.330000"),
            ),
            input_row(
                "research.policy.hearing.ai",
                condition_id="condition_policy_hearing_ai",
                policy_area="ai_oversight",
                hearing_id="hearing_ai_oversight",
                public_schedule_reference="confidential-hearing-brief",
                hearing_scheduled_at=GENERATED_AT + timedelta(hours=12),
                schedule_observed_at=GENERATED_AT - timedelta(hours=3),
                confirmed_at=None,
                public_source_count=d("2"),
                cross_source_agreement=d("0.700000"),
                schedule_materiality_score=d("0.420000"),
                market_probability_before=d("0.460000"),
                market_probability_after=d("0.610000"),
            ),
            input_row(
                "research.policy.hearing.energy",
                condition_id="condition_policy_hearing_energy",
                policy_area="energy_permitting",
                hearing_id="hearing_energy_permitting",
                public_schedule_reference="public-hearing-notice",
                hearing_scheduled_at=GENERATED_AT + timedelta(days=7),
                schedule_observed_at=GENERATED_AT - timedelta(minutes=45),
                confirmed_at=GENERATED_AT - timedelta(minutes=15),
                public_source_count=d("3"),
                cross_source_agreement=d("0.800000"),
                schedule_materiality_score=d("0.120000"),
                market_probability_before=d("0.420000"),
                market_probability_after=d("0.500000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_POLICY_HEARING_SCHEDULE_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_hearing_schedule_digest"
    )
    assert summary.hearing_count == d("3.000000")
    assert summary.ready_hearing_count == d("1.000000")
    assert summary.watch_hearing_count == d("1.000000")
    assert summary.blocked_hearing_count == d("1.000000")
    assert summary.material_hearing_count == d("2.000000")
    assert summary.near_hearing_count == d("1.000000")
    assert summary.past_hearing_count == d("1.000000")
    assert summary.stale_schedule_count == d("1.000000")
    assert summary.thin_source_count == d("1.000000")
    assert summary.low_agreement_count == d("1.000000")
    assert summary.missing_confirmation_count == d("1.000000")
    assert summary.stale_confirmation_count == d("1.000000")
    assert summary.average_materiality_score == d("0.246667")
    assert summary.min_seconds_until_hearing == d("-10800.000000")
    assert summary.average_public_source_count == d("2.000000")
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True

    assert tuple((row.hearing_status, row.policy_area) for row in summary.rows) == (
        ("blocked", "ai_oversight"),
        ("watch", "archived_tax_rules"),
        ("ready", "energy_permitting"),
    )

    blocked = summary.rows[0]
    assert blocked.schedule_age_seconds == d("10800.000000")
    assert blocked.seconds_until_hearing == d("43200.000000")
    assert blocked.confirmation_lag_seconds is None
    assert blocked.probability_change == d("0.150000")
    assert blocked.redacted_schedule_reference == "sha256:5236b283d86c"
    assert blocked.reason_codes == (
        "market_research_policy_hearing_schedule_digest_material_block",
        "market_research_policy_hearing_schedule_digest_missing_confirmation",
        "market_research_policy_hearing_schedule_digest_near_hearing",
        "market_research_policy_hearing_schedule_digest_probability_shift",
    )

    watch = summary.rows[1]
    assert watch.schedule_age_seconds == d("108000.000000")
    assert watch.seconds_until_hearing == d("-10800.000000")
    assert watch.confirmation_lag_seconds == d("82800.000000")
    assert watch.redacted_schedule_reference == "sha256:e5e1bb0a97c8"
    assert watch.reason_codes == (
        "market_research_policy_hearing_schedule_digest_low_agreement",
        "market_research_policy_hearing_schedule_digest_material_watch",
        "market_research_policy_hearing_schedule_digest_past_hearing",
        "market_research_policy_hearing_schedule_digest_stale_confirmation",
        "market_research_policy_hearing_schedule_digest_stale_schedule",
        "market_research_policy_hearing_schedule_digest_thin_sources",
    )

    ready = summary.rows[2]
    assert ready.hearing_status == "ready"
    assert ready.schedule_age_seconds == d("2700.000000")
    assert ready.seconds_until_hearing == d("604800.000000")
    assert ready.confirmation_lag_seconds == d("1800.000000")
    assert ready.redacted_schedule_reference == "public-hearing-notice"
    assert ready.reason_codes == (
        "market_research_policy_hearing_schedule_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_material_block",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_missing_confirmation",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_near_hearing",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_probability_shift",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_low_agreement",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_material_watch",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_past_hearing",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_stale_confirmation",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_stale_schedule",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_thin_sources",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_ready",
            count=d("1.000000"),
            hearing_ratio=d("0.333333"),
        ),
    )
    assert summary.reason_codes == tuple(
        row.reason_code for row in summary.reason_code_counts
    )

    public = repr(asdict(summary)).lower()
    for value in (
        "hidden",
        "calendar.example",
        "https://",
        "confidential-hearing-brief",
        "token",
    ):
        assert value not in public


def test_empty_policy_hearing_schedule_digest_is_blocked_and_report_only() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.next_step == (
        "block_report_only_market_research_policy_hearing_schedule_digest"
    )
    assert summary.hearing_count == ZERO
    assert summary.ready_hearing_count == ZERO
    assert summary.watch_hearing_count == ZERO
    assert summary.blocked_hearing_count == ZERO
    assert summary.average_materiality_score == ZERO
    assert summary.min_seconds_until_hearing == ZERO
    assert summary.average_public_source_count == ZERO
    assert summary.rows == ()
    assert summary.reason_code_counts == (
            MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
                reason_code="market_research_policy_hearing_schedule_digest_no_inputs",
                count=d("1.000000"),
                hearing_ratio=ZERO,
            ),
        )
    assert summary.reason_codes == (
        "market_research_policy_hearing_schedule_digest_no_inputs",
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_policy_hearing_schedule_payload_uses_decimal_strings_and_redacts() -> None:
    summary = report((input_row(),))
    payload = market_research_policy_hearing_schedule_digest_payload(summary)
    json.dumps(payload, sort_keys=True)

    assert payload["hearing_count"] == "1.000000"
    assert payload["average_materiality_score"] == "0.120000"
    assert payload["rows"][0]["public_source_count"] == "3.000000"
    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert not any(isinstance(value, float) for value in walk_values(payload))
    assert "'public_schedule_reference':" not in repr(payload)
    assert "confidential" not in repr(payload).lower()


def test_payload_rejects_tampered_non_utc_datetimes() -> None:
    summary = report((input_row(),))
    object.__setattr__(
        summary,
        "generated_at",
        GENERATED_AT.astimezone(timezone(timedelta(hours=-4))),
    )

    with pytest.raises(ValueError, match="generated_at"):
        market_research_policy_hearing_schedule_digest_payload(summary)

    summary = report((input_row(),))
    object.__setattr__(
        summary.rows[0],
        "schedule_observed_at",
        summary.rows[0].schedule_observed_at.astimezone(
            timezone(timedelta(hours=2)),
        ),
    )

    with pytest.raises(ValueError, match="schedule_observed_at"):
        market_research_policy_hearing_schedule_digest_payload(summary)


def test_payload_revalidates_nested_report_only_flags() -> None:
    summary = report((input_row(),))
    object.__setattr__(summary.rows[0], "report_only", False)

    with pytest.raises(ValueError, match="report_only"):
        market_research_policy_hearing_schedule_digest_payload(summary)

    summary = report((input_row(),))
    object.__setattr__(summary.reason_code_counts[0], "readonly", False)

    with pytest.raises(ValueError, match="readonly"):
        market_research_policy_hearing_schedule_digest_payload(summary)


def test_payload_rejects_tampered_non_six_decimal_values() -> None:
    summary = report((input_row(),))
    object.__setattr__(summary.rows[0], "public_source_count", Decimal("3"))

    with pytest.raises(ValueError, match="public_source_count"):
        market_research_policy_hearing_schedule_digest_payload(summary)

    summary = report((input_row(),))
    object.__setattr__(summary.reason_code_counts[0], "hearing_ratio", Decimal("1"))

    with pytest.raises(ValueError, match="hearing_ratio"):
        market_research_policy_hearing_schedule_digest_payload(summary)


def test_rejects_tzinfo_without_utc_offset() -> None:
    no_offset_datetime = datetime(2026, 7, 4, 12, 0, tzinfo=_NoneOffsetTz())

    with pytest.raises(ValueError, match="hearing_scheduled_at"):
        input_row(hearing_scheduled_at=no_offset_datetime)

    with pytest.raises(ValueError, match="generated_at"):
        report((), generated_at=no_offset_datetime)


def test_reason_code_count_rejects_manual_zero_count() -> None:
    with pytest.raises(ValueError, match="count"):
        MarketResearchPolicyHearingScheduleDigestReasonCodeCount(
            reason_code="market_research_policy_hearing_schedule_digest_ready",
            count=ZERO,
            hearing_ratio=ZERO,
        )


def test_payload_rejects_raw_containers_and_unknown_public_objects() -> None:
    for value in ([], {}, set(), object(), input_row()):
        with pytest.raises(ValueError, match="report"):
            market_research_policy_hearing_schedule_digest_payload(value)  # type: ignore[arg-type]


def test_public_dataclasses_are_frozen_exact_type_and_not_subclassable() -> None:
    for public_dataclass in PUBLIC_DATACLASSES:
        assert public_dataclass.__dataclass_params__.frozen is True
        with pytest.raises(TypeError, match="subclassing"):
            type(f"Sub{public_dataclass.__name__}", (public_dataclass,), {})


def test_policy_hearing_schedule_rejects_explicit_false_flags() -> None:
    for field_name in ("paper_only", "report_only", "readonly"):
        with pytest.raises(ValueError, match=field_name):
            config(**{field_name: False})
        with pytest.raises(ValueError, match=field_name):
            input_row(**{field_name: False})
        with pytest.raises(ValueError, match=field_name):
            replace(report((input_row(),)), **{field_name: False})


def test_policy_hearing_schedule_constructor_ordering_is_deterministic() -> None:
    rows = (
        input_row(
            "research.policy.hearing.zeta",
            condition_id="condition_policy_hearing_zeta",
            policy_area="zeta_rules",
            hearing_id="hearing_zeta_rules",
            hearing_scheduled_at=GENERATED_AT + timedelta(days=3),
        ),
        input_row(
            "research.policy.hearing.alpha",
            condition_id="condition_policy_hearing_alpha",
            policy_area="alpha_rules",
            hearing_id="hearing_alpha_rules",
            hearing_scheduled_at=GENERATED_AT + timedelta(days=1),
        ),
    )

    forward = market_research_policy_hearing_schedule_digest_payload(report(rows))
    reverse = market_research_policy_hearing_schedule_digest_payload(
        report(tuple(reversed(rows))),
    )

    assert json.dumps(forward, sort_keys=True) == json.dumps(reverse, sort_keys=True)


def test_payload_path_does_not_use_dataclasses_asdict() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    for node in ast.walk(tree):
        if isinstance(node, ast.ImportFrom) and node.module == "dataclasses":
            assert all(alias.name != "asdict" for alias in node.names)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id != "asdict"
            elif isinstance(node.func, ast.Attribute):
                assert node.func.attr != "asdict"


def test_policy_hearing_schedule_validates_public_contracts_and_flags() -> None:
    assert is_dataclass(MarketResearchPolicyHearingScheduleDigestConfig)
    assert is_dataclass(MarketResearchPolicyHearingScheduleDigestInputRow)
    assert is_dataclass(MarketResearchPolicyHearingScheduleDigestRow)
    assert is_dataclass(MarketResearchPolicyHearingScheduleDigestReasonCodeCount)
    assert is_dataclass(MarketResearchPolicyHearingScheduleDigestReport)

    summary = report((input_row(),))
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].public_source_count = d("4")  # type: ignore[misc]

    with pytest.raises(ValueError, match="config_version"):
        config(config_version=_StringSubclass("hearing-schedule-v0"))
    with pytest.raises(ValueError, match="fresh_schedule_max_age_seconds"):
        config(fresh_schedule_max_age_seconds=86400)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="min_public_source_count"):
        config(min_public_source_count=d("1.5"))
    with pytest.raises(ValueError, match="min_cross_source_agreement"):
        config(min_cross_source_agreement=Decimal("NaN"))
    with pytest.raises(ValueError, match="materiality_watch_threshold"):
        config(materiality_watch_threshold=d("-0.000001"))
    with pytest.raises(ValueError, match="materiality_block_threshold"):
        config(
            materiality_watch_threshold=d("0.500000"),
            materiality_block_threshold=d("0.350000"),
        )
    with pytest.raises(ValueError, match="research_key"):
        input_row(" bad")
    with pytest.raises(ValueError, match="condition_id"):
        input_row(condition_id="live_surface")
    with pytest.raises(ValueError, match="hearing_id"):
        input_row(hearing_id="")
    with pytest.raises(ValueError, match="hearing_scheduled_at"):
        input_row(hearing_scheduled_at=datetime(2026, 7, 4, 12, 0))
    with pytest.raises(ValueError, match="confirmed_at"):
        input_row(confirmed_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC))
    with pytest.raises(ValueError, match="public_source_count"):
        input_row(public_source_count=2)  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="cross_source_agreement"):
        input_row(cross_source_agreement=_DecimalSubclass("0.700000"))
    with pytest.raises(ValueError, match="schedule_materiality_score"):
        input_row(schedule_materiality_score=Decimal("Infinity"))
    with pytest.raises(ValueError, match="market_probability_before"):
        input_row(market_probability_before=d("1.000001"))
    with pytest.raises(ValueError, match="market_probability_after"):
        input_row(market_probability_after=d("-0.000001"))
    with pytest.raises(ValueError, match="paper_only"):
        input_row(paper_only=False)
    with pytest.raises(ValueError, match="config"):
        build_market_research_policy_hearing_schedule_digest(
            (),
            config=object(),  # type: ignore[arg-type]
            generated_at=GENERATED_AT,
        )
    with pytest.raises(ValueError, match="generated_at"):
        build_market_research_policy_hearing_schedule_digest(
            (),
            config=config(),
            generated_at=_DateTimeSubclass(2026, 7, 4, 12, 0, tzinfo=UTC),
        )
    with pytest.raises(ValueError, match="input rows"):
        report((object(),))


def test_report_and_row_consistency_rejects_manual_drift() -> None:
    ready = report((input_row(),)).rows[0]

    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            ready,
            reason_codes=(
                "market_research_policy_hearing_schedule_digest_ready",
                "market_research_policy_hearing_schedule_digest_material_watch",
            ),
        )
    with pytest.raises(ValueError, match="hearing_status"):
        replace(ready, hearing_status="blocked")
    with pytest.raises(ValueError, match="probability_change"):
        replace(ready, probability_change=d("9.999999"))
    with pytest.raises(ValueError, match="redacted_schedule_reference"):
        replace(ready, redacted_schedule_reference="https://host?token=hidden")
    with pytest.raises(ValueError, match="confirmation_lag_seconds"):
        replace(ready, confirmation_lag_seconds=d("999.000000"))

    unconfirmed = report((input_row(confirmed_at=None),)).rows[0]
    with pytest.raises(ValueError, match="confirmation_lag_seconds"):
        replace(unconfirmed, confirmation_lag_seconds=d("1.000000"))

    with pytest.raises(ValueError, match="ready_hearing_count"):
        replace(report((input_row(),)), ready_hearing_count=ZERO)
    with pytest.raises(ValueError, match="rows"):
        unordered = report(
            (
                input_row("research.policy.hearing.z", policy_area="zeta_rules"),
                input_row(),
            ),
        )
        replace(unordered, rows=tuple(reversed(unordered.rows)))


def test_public_numeric_fields_are_decimals() -> None:
    summary = report((input_row(),))

    assert_decimal_numeric_fields(summary)
    assert_decimal_numeric_fields(summary.rows[0])
    assert_decimal_numeric_fields(summary.reason_code_counts[0])


def test_module_has_no_io_store_or_execution_surfaces() -> None:
    source = MODULE_PATH.read_text(encoding="utf-8")
    tree = ast.parse(source)

    imported_modules: list[str] = []
    call_names: list[str] = []
    attribute_names: list[str] = []

    for node in ast.walk(tree):
        if isinstance(node, ast.Import):
            imported_modules.extend(alias.name for alias in node.names)
        elif isinstance(node, ast.ImportFrom) and node.module is not None:
            imported_modules.append(node.module)
        elif isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                call_names.append(node.func.id)
            elif isinstance(node.func, ast.Attribute):
                call_names.append(node.func.attr)
        elif isinstance(node, ast.Attribute):
            attribute_names.append(node.attr)
        elif isinstance(node, ast.Constant):
            assert type(node.value) is not float

    forbidden_import_roots = {
        "os",
        "pathlib",
        "socket",
        "subprocess",
        "requests",
        "httpx",
        "sqlite3",
        "psycopg",
        "supabase",
    }
    forbidden_calls = {
        "connect",
        "execute",
        "open",
        "request",
        "write_bytes",
        "write_text",
        "float",
        "__import__",
    }
    forbidden_fragments = (
        "live_trading",
        "auth",
        "wallet",
        "broker",
        "cancel",
        "signing",
        "advice",
        "market_slug",
        "question",
        "private_key",
        "api_key",
        "secret",
        "position",
        "trade",
        "bet",
        "stake",
        "client",
        "requests",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
        "network",
        "database",
        "durable",
    )

    for module_name in imported_modules:
        assert module_name.split(".", 1)[0] not in forbidden_import_roots
    for call_name in call_names:
        assert call_name not in forbidden_calls
    for attr_name in attribute_names:
        assert attr_name not in forbidden_calls

    lowered = source.lower()
    for value in forbidden_fragments:
        assert value not in lowered
