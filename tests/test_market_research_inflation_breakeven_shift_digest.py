from __future__ import annotations

import ast
import re
from dataclasses import FrozenInstanceError, dataclass, fields, is_dataclass, replace
from datetime import UTC, datetime, timedelta, timezone, tzinfo
from decimal import Decimal
from pathlib import Path

import pytest

import polymarket_alpha_lab.market_research_inflation_breakeven_shift_digest as digest_module
from polymarket_alpha_lab.market_research_inflation_breakeven_shift_digest import (
    DEFAULT_MARKET_RESEARCH_INFLATION_BREAKEVEN_SHIFT_DIGEST_CONFIG_VERSION,
    MarketResearchInflationBreakevenShiftDigestConfig,
    MarketResearchInflationBreakevenShiftDigestReasonCodeCount,
    MarketResearchInflationBreakevenShiftDigestReport,
    MarketResearchInflationBreakevenShiftDigestRow,
    MarketResearchInflationBreakevenShiftDigestSignal,
    build_market_research_inflation_breakeven_shift_digest,
    market_research_inflation_breakeven_shift_digest_payload,
)


GENERATED_AT = datetime(2026, 7, 2, 12, 0, tzinfo=UTC)
ZERO = Decimal("0.000000")


class _DatetimeSubclass(datetime):
    pass


class _DecimalSubclass(Decimal):
    pass


class _StringSubclass(str):
    pass


@dataclass(frozen=True)
class _UnknownPublicRecord:
    paper_only: bool = True
    report_only: bool = True
    readonly: bool = True


class _UnknownPublicObject:
    paper_only = True
    report_only = True
    readonly = True


class _NoneOffsetTimezone(tzinfo):
    def utcoffset(self, dt: datetime | None) -> None:
        return None

    def dst(self, dt: datetime | None) -> None:
        return None


def d(value: str) -> Decimal:
    return Decimal(value)


def config(
    **overrides: object,
) -> MarketResearchInflationBreakevenShiftDigestConfig:
    values = {
        "config_version": (
            DEFAULT_MARKET_RESEARCH_INFLATION_BREAKEVEN_SHIFT_DIGEST_CONFIG_VERSION
        ),
        "max_signal_age_seconds": d("7200.000000"),
        "min_breakeven_shift_abs": d("0.050000"),
        "max_market_probability_gap_abs": d("0.100000"),
        "min_source_family_count": d("3.000000"),
        "max_stale_source_ratio": d("0.250000"),
        "min_confirmation_ratio": d("0.650000"),
        "confidence_decay_per_gap": d("0.100000"),
        "watch_confidence_threshold": d("0.650000"),
    }
    values.update(overrides)
    return MarketResearchInflationBreakevenShiftDigestConfig(**values)


def signal(
    condition_id: str = "condition.alpha",
    *,
    breakeven_key: str = "tips.5y5y.forward",
    public_signal_reference: str = "treasury-tips-release",
    observed_at: datetime | None = None,
    signal_age_seconds: Decimal = d("900.000000"),
    breakeven_shift: Decimal = d("0.080000"),
    market_probability_gap: Decimal = d("0.040000"),
    source_family_count: Decimal = d("3.000000"),
    stale_source_ratio: Decimal = d("0.100000"),
    confirmation_ratio: Decimal = d("0.800000"),
    base_confidence: Decimal = d("0.850000"),
    signal_config_version: str = "inflation-breakeven-shift-v0",
    paper_only: bool = True,
    report_only: bool = True,
    readonly: bool = True,
) -> MarketResearchInflationBreakevenShiftDigestSignal:
    return MarketResearchInflationBreakevenShiftDigestSignal(
        condition_id=condition_id,
        breakeven_key=breakeven_key,
        public_signal_reference=public_signal_reference,
        observed_at=observed_at or GENERATED_AT - timedelta(minutes=15),
        signal_age_seconds=signal_age_seconds,
        breakeven_shift=breakeven_shift,
        market_probability_gap=market_probability_gap,
        source_family_count=source_family_count,
        stale_source_ratio=stale_source_ratio,
        confirmation_ratio=confirmation_ratio,
        base_confidence=base_confidence,
        signal_config_version=signal_config_version,
        paper_only=paper_only,
        report_only=report_only,
        readonly=readonly,
    )


def report(
    signals: tuple[object, ...],
    *,
    cfg: MarketResearchInflationBreakevenShiftDigestConfig | None = None,
    generated_at: datetime = GENERATED_AT,
) -> MarketResearchInflationBreakevenShiftDigestReport:
    return build_market_research_inflation_breakeven_shift_digest(
        signals,
        config=config() if cfg is None else cfg,
        generated_at=generated_at,
    )


def test_breakeven_shift_digest_reduces_signals_and_redacts_references() -> None:
    summary = report(
        (
            signal(
                "condition.stale",
                breakeven_key="tips.10y.headline",
                public_signal_reference=(
                    "https://macro.example/breakeven?token=secret-123"
                ),
                observed_at=GENERATED_AT - timedelta(hours=3),
                signal_age_seconds=d("9000.000000"),
                breakeven_shift=d("0.020000"),
                market_probability_gap=d("0.180000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
            signal(
                "condition.partial",
                breakeven_key="tips.5y.forward",
                public_signal_reference="wallet://private/tips-note",
                breakeven_shift=d("-0.070000"),
                market_probability_gap=d("0.060000"),
                source_family_count=d("3.000000"),
                stale_source_ratio=d("0.100000"),
                confirmation_ratio=d("0.550000"),
                base_confidence=d("0.760000"),
            ),
            signal(
                "condition.ready",
                breakeven_key="tips.2y.ready",
                public_signal_reference="public-treasury-tips-series",
                breakeven_shift=d("0.090000"),
                market_probability_gap=d("0.020000"),
                source_family_count=d("4.000000"),
                stale_source_ratio=d("0.050000"),
                confirmation_ratio=d("0.840000"),
                base_confidence=d("0.880000"),
            ),
        ),
        generated_at=GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )

    assert isinstance(summary, MarketResearchInflationBreakevenShiftDigestReport)
    assert is_dataclass(summary)
    assert summary.generated_at == GENERATED_AT
    assert summary.generated_at.tzinfo is UTC
    assert summary.config_version == (
        DEFAULT_MARKET_RESEARCH_INFLATION_BREAKEVEN_SHIFT_DIGEST_CONFIG_VERSION
    )
    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_inflation_breakeven_shift_digest"
    )
    assert summary.signal_count == d("3.000000")
    assert summary.ready_signal_count == d("1.000000")
    assert summary.watch_signal_count == d("1.000000")
    assert summary.blocked_signal_count == d("1.000000")
    assert summary.stale_signal_count == d("1.000000")
    assert summary.low_breakeven_shift_signal_count == d("1.000000")
    assert summary.market_probability_gap_signal_count == d("1.000000")
    assert summary.source_family_gap_signal_count == d("1.000000")
    assert summary.stale_source_signal_count == d("1.000000")
    assert summary.confirmation_gap_signal_count == d("2.000000")
    assert summary.total_confidence_decay == d("0.700000")
    assert summary.average_final_confidence == d("0.613333")
    assert summary.average_breakeven_shift_abs == d("0.060000")
    assert summary.average_market_probability_gap_abs == d("0.086667")
    assert summary.average_confirmation_ratio == d("0.596667")
    assert summary.max_observed_signal_age_seconds == d("10800.000000")
    assert tuple(row.breakeven_key for row in summary.rows) == (
        "tips.10y.headline",
        "tips.5y.forward",
        "tips.2y.ready",
    )

    stale = summary.rows[0]
    assert stale.digest_status == "blocked"
    assert stale.signal_age_seconds == d("10800.000000")
    assert stale.breakeven_shift_abs == d("0.020000")
    assert stale.market_probability_gap_abs == d("0.180000")
    assert stale.confidence_decay_factor == d("0.600000")
    assert stale.final_confidence == d("0.300000")
    assert stale.redacted_public_signal_reference == "sha256:a136069bd475"
    assert stale.reason_codes == (
        "market_research_inflation_breakeven_shift_digest_stale_signal",
        "market_research_inflation_breakeven_shift_digest_low_breakeven_shift",
        "market_research_inflation_breakeven_shift_digest_market_probability_gap",
        "market_research_inflation_breakeven_shift_digest_source_family_gap",
        "market_research_inflation_breakeven_shift_digest_stale_source_ratio",
        "market_research_inflation_breakeven_shift_digest_confirmation_gap",
    )

    partial = summary.rows[1]
    assert partial.digest_status == "watch"
    assert partial.breakeven_shift_abs == d("0.070000")
    assert partial.market_probability_gap_abs == d("0.060000")
    assert partial.confidence_decay_factor == d("0.100000")
    assert partial.final_confidence == d("0.660000")
    assert partial.redacted_public_signal_reference == "sha256:362c3119baf8"
    assert partial.reason_codes == (
        "market_research_inflation_breakeven_shift_digest_confirmation_gap",
    )

    ready = summary.rows[2]
    assert ready.digest_status == "ready"
    assert ready.final_confidence == d("0.880000")
    assert ready.redacted_public_signal_reference == "public-treasury-tips-series"
    assert ready.reason_codes == (
        "market_research_inflation_breakeven_shift_digest_ready",
    )

    assert summary.reason_code_counts == (
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_inflation_breakeven_shift_digest_confirmation_gap"
            ),
            count=d("2.000000"),
            signal_ratio=d("0.666667"),
        ),
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code="market_research_inflation_breakeven_shift_digest_stale_signal",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_inflation_breakeven_shift_digest_low_breakeven_shift"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_inflation_breakeven_shift_digest_market_probability_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_inflation_breakeven_shift_digest_source_family_gap"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code=(
                "market_research_inflation_breakeven_shift_digest_stale_source_ratio"
            ),
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code="market_research_inflation_breakeven_shift_digest_ready",
            count=d("1.000000"),
            signal_ratio=d("0.333333"),
        ),
    )


def test_empty_digest_is_readonly_blocked_report_with_decimal_counts() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.recommended_next_step == (
        "block_report_only_market_research_inflation_breakeven_shift_digest"
    )
    assert summary.signal_count == ZERO
    assert summary.ready_signal_count == ZERO
    assert summary.watch_signal_count == ZERO
    assert summary.blocked_signal_count == ZERO
    assert summary.total_confidence_decay == ZERO
    assert summary.average_final_confidence == ZERO
    assert summary.average_breakeven_shift_abs == ZERO
    assert summary.average_market_probability_gap_abs == ZERO
    assert summary.average_confirmation_ratio == ZERO
    assert summary.max_observed_signal_age_seconds == ZERO
    assert summary.rows == ()
    assert summary.reason_codes == (
        "market_research_inflation_breakeven_shift_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code="market_research_inflation_breakeven_shift_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )
    assert summary.paper_only is True
    assert summary.report_only is True
    assert summary.readonly is True


def test_empty_digest_blocks_as_missing_evidence() -> None:
    summary = report(())

    assert summary.digest_status == "blocked"
    assert summary.reason_codes == (
        "market_research_inflation_breakeven_shift_digest_no_inputs",
    )
    assert summary.reason_code_counts == (
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code="market_research_inflation_breakeven_shift_digest_no_inputs",
            count=d("1.000000"),
            signal_ratio=ZERO,
        ),
    )


def test_reason_code_count_rejects_zero_manual_count() -> None:
    with pytest.raises(ValueError, match="count must be positive"):
        MarketResearchInflationBreakevenShiftDigestReasonCodeCount(
            reason_code="market_research_inflation_breakeven_shift_digest_ready",
            count=ZERO,
            signal_ratio=ZERO,
        )


def test_digest_dataclasses_are_frozen_and_public_numbers_are_decimal() -> None:
    summary = report((signal(),))

    with pytest.raises(FrozenInstanceError):
        summary.digest_status = "blocked"  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        summary.rows[0].final_confidence = ZERO  # type: ignore[misc]
    with pytest.raises(FrozenInstanceError):
        config().max_signal_age_seconds = ZERO  # type: ignore[misc]

    for value in (config(), signal(), summary.rows[0], summary.reason_code_counts[0], summary):
        assert is_dataclass(value)
        for item_field in fields(value):
            if item_field.name in {"paper_only", "report_only", "readonly"}:
                continue
            item = getattr(value, item_field.name)
            if (
                item_field.name.endswith("_count")
                or item_field.name.endswith("_ratio")
                or item_field.name.endswith("_seconds")
                or item_field.name.endswith("_confidence")
                or item_field.name.endswith("_decay")
                or item_field.name.endswith("_shift")
                or item_field.name.endswith("_shift_abs")
                or item_field.name.endswith("_gap")
                or item_field.name.endswith("_gap_abs")
            ):
                assert type(item) is Decimal, item_field.name


def test_payload_is_json_safe_deterministic_and_has_only_report_scope() -> None:
    summary = report(
        (
            signal("condition.b", breakeven_key="tips.z"),
            signal("condition.a", breakeven_key="tips.a"),
        ),
    )

    payload = market_research_inflation_breakeven_shift_digest_payload(summary)

    assert payload["paper_only"] is True
    assert payload["report_only"] is True
    assert payload["readonly"] is True
    assert payload["generated_at"] == "2026-07-02T12:00:00+00:00"
    assert payload["signal_count"] == "2.000000"
    assert payload["average_final_confidence"] == "0.850000"
    assert payload["max_observed_signal_age_seconds"] == "900.000000"
    assert tuple(row["condition_id"] for row in payload["rows"]) == (
        "condition.a",
        "condition.b",
    )
    assert payload["reason_codes"] == tuple(sorted(payload["reason_codes"]))
    assert payload["rows"][0]["observed_at"] == "2026-07-02T11:45:00+00:00"
    assert payload["rows"][0]["final_confidence"] == "0.850000"
    assert payload["rows"][0]["breakeven_shift"] == "0.080000"

    def walk(value: object) -> None:
        if isinstance(value, dict):
            for child in value.values():
                walk(child)
        elif isinstance(value, (list, tuple)):
            for child in value:
                walk(child)
        else:
            assert not isinstance(value, (Decimal, datetime, float))
            if isinstance(value, str) and re.fullmatch(r"-?\d+\.\d{6}", value):
                assert Decimal(value) == Decimal(value).quantize(d("0.000001"))

    walk(payload)


def test_payload_revalidates_tampered_nested_dataclasses_and_flags() -> None:
    report_flag_summary = report((signal(),))
    object.__setattr__(report_flag_summary, "readonly", False)
    with pytest.raises(ValueError, match="readonly"):
        market_research_inflation_breakeven_shift_digest_payload(report_flag_summary)

    row_flag_summary = report((signal(),))
    object.__setattr__(row_flag_summary.rows[0], "paper_only", False)
    with pytest.raises(ValueError, match="paper_only"):
        market_research_inflation_breakeven_shift_digest_payload(row_flag_summary)

    reason_flag_summary = report((signal(),))
    object.__setattr__(reason_flag_summary.reason_code_counts[0], "report_only", False)
    with pytest.raises(ValueError, match="report_only"):
        market_research_inflation_breakeven_shift_digest_payload(reason_flag_summary)

    nested_type_summary = report((signal(),))
    object.__setattr__(nested_type_summary, "rows", ({"condition_id": "condition.alpha"},))
    with pytest.raises(ValueError, match="rows"):
        market_research_inflation_breakeven_shift_digest_payload(nested_type_summary)

    report_datetime_summary = report((signal(),))
    object.__setattr__(
        report_datetime_summary,
        "generated_at",
        GENERATED_AT.astimezone(timezone(timedelta(hours=-5))),
    )
    with pytest.raises(ValueError, match="generated_at must be UTC"):
        market_research_inflation_breakeven_shift_digest_payload(report_datetime_summary)

    row_datetime_summary = report((signal(),))
    object.__setattr__(
        row_datetime_summary.rows[0],
        "observed_at",
        (GENERATED_AT - timedelta(minutes=15)).astimezone(
            timezone(timedelta(hours=-5)),
        ),
    )
    with pytest.raises(ValueError, match="observed_at must be UTC"):
        market_research_inflation_breakeven_shift_digest_payload(row_datetime_summary)


def test_payload_rejects_tampered_non_six_decimal_values() -> None:
    count_type_summary = report((signal(),))
    object.__setattr__(count_type_summary, "signal_count", 1)
    with pytest.raises(ValueError, match="signal_count"):
        market_research_inflation_breakeven_shift_digest_payload(count_type_summary)

    row_decimal_summary = report((signal(),))
    object.__setattr__(row_decimal_summary.rows[0], "final_confidence", d("0.8500001"))
    with pytest.raises(ValueError, match="final_confidence"):
        market_research_inflation_breakeven_shift_digest_payload(row_decimal_summary)

    reason_decimal_summary = report((signal(),))
    object.__setattr__(
        reason_decimal_summary.reason_code_counts[0],
        "signal_ratio",
        d("1.0000000"),
    )
    with pytest.raises(ValueError, match="signal_ratio"):
        market_research_inflation_breakeven_shift_digest_payload(reason_decimal_summary)


def test_payload_serializer_revalidates_direct_public_dataclass_invariants() -> None:
    reason_count = report((signal(),)).reason_code_counts[0]
    object.__setattr__(reason_count, "count", ZERO)

    with pytest.raises(ValueError, match="count must be positive"):
        digest_module._serialize_for_output(reason_count)  # type: ignore[attr-defined]


def test_payload_serializer_rejects_raw_containers_and_unknown_public_records() -> None:
    for raw_container in ([], {}, set()):
        with pytest.raises(ValueError, match="raw container"):
            digest_module._serialize_for_output(raw_container)  # type: ignore[attr-defined]

    with pytest.raises(ValueError, match="unknown public dataclass"):
        digest_module._serialize_for_output(_UnknownPublicRecord())  # type: ignore[attr-defined]

    with pytest.raises(ValueError, match="unknown public object"):
        digest_module._serialize_for_output(_UnknownPublicObject())  # type: ignore[attr-defined]


def test_validation_rejects_non_canonical_types_and_false_scope_flags() -> None:
    with pytest.raises(TypeError, match="subclassing"):
        type("ConfigSubclass", (MarketResearchInflationBreakevenShiftDigestConfig,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("SignalSubclass", (MarketResearchInflationBreakevenShiftDigestSignal,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type("RowSubclass", (MarketResearchInflationBreakevenShiftDigestRow,), {})
    with pytest.raises(TypeError, match="subclassing"):
        type(
            "ReasonCodeCountSubclass",
            (MarketResearchInflationBreakevenShiftDigestReasonCodeCount,),
            {},
        )
    with pytest.raises(TypeError, match="subclassing"):
        type("ReportSubclass", (MarketResearchInflationBreakevenShiftDigestReport,), {})

    with pytest.raises(ValueError, match="generated_at must be a datetime"):
        report((signal(),), generated_at=_DatetimeSubclass(2026, 7, 2, tzinfo=UTC))
    with pytest.raises(ValueError, match="observed_at must be a datetime"):
        signal(observed_at=_DatetimeSubclass(2026, 7, 2, tzinfo=UTC))
    with pytest.raises(ValueError, match="generated_at must be timezone-aware"):
        report(
            (signal(),),
            generated_at=datetime(2026, 7, 2, tzinfo=_NoneOffsetTimezone()),
        )
    with pytest.raises(ValueError, match="observed_at must be timezone-aware"):
        signal(observed_at=datetime(2026, 7, 2, tzinfo=_NoneOffsetTimezone()))
    with pytest.raises(ValueError, match="breakeven_shift must be exactly Decimal"):
        signal(breakeven_shift=_DecimalSubclass("0.100000"))
    with pytest.raises(ValueError, match="condition_id must be a non-empty string"):
        signal(condition_id=_StringSubclass("condition.subclass"))
    with pytest.raises(ValueError, match="condition_id"):
        signal(condition_id="condition-order-flow")
    with pytest.raises(ValueError, match="breakeven_key"):
        signal(breakeven_key="tips.wallet.flow")
    with pytest.raises(ValueError, match="signal_config_version"):
        signal(signal_config_version="config-auth-surface")
    with pytest.raises(ValueError, match="paper_only must be True"):
        config(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        config(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        config(readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        signal(paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        signal(report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        signal(readonly=False)

    summary = report((signal(),))
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(summary.rows[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(summary.rows[0], report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(summary.rows[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(summary.reason_code_counts[0], paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(summary.reason_code_counts[0], report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(summary.reason_code_counts[0], readonly=False)
    with pytest.raises(ValueError, match="paper_only must be True"):
        replace(summary, paper_only=False)
    with pytest.raises(ValueError, match="report_only must be True"):
        replace(summary, report_only=False)
    with pytest.raises(ValueError, match="readonly must be True"):
        replace(summary, readonly=False)


def test_manual_breakeven_rows_keep_deterministic_order_and_reason_codes() -> None:
    summary = report(
        (
            signal("condition.b", breakeven_key="tips.z"),
            signal("condition.a", breakeven_key="tips.a"),
        ),
    )

    with pytest.raises(ValueError, match="rows"):
        replace(summary, rows=tuple(reversed(summary.rows)))
    with pytest.raises(ValueError, match="signal_config_versions"):
        replace(
            summary,
            signal_config_versions=tuple(reversed(summary.signal_config_versions)),
        )

    watch_summary = report(
        (
            signal(
                "condition.watch",
                breakeven_key="tips.watch",
                confirmation_ratio=d("0.500000"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(watch_summary.rows[0], reason_codes=())

    multi_reason_summary = report(
        (
            signal(
                "condition.blocked",
                breakeven_key="tips.blocked",
                observed_at=GENERATED_AT - timedelta(hours=3),
                breakeven_shift=d("0.020000"),
                market_probability_gap=d("0.180000"),
                source_family_count=d("2.000000"),
                stale_source_ratio=d("0.400000"),
                confirmation_ratio=d("0.400000"),
                base_confidence=d("0.900000"),
            ),
        ),
    )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            multi_reason_summary.rows[0],
            reason_codes=tuple(reversed(multi_reason_summary.rows[0].reason_codes)),
        )
    with pytest.raises(ValueError, match="reason_code_counts"):
        replace(
            multi_reason_summary,
            reason_code_counts=tuple(reversed(multi_reason_summary.reason_code_counts)),
        )
    with pytest.raises(ValueError, match="reason_codes"):
        replace(
            multi_reason_summary,
            reason_codes=tuple(reversed(multi_reason_summary.reason_codes)),
        )


def test_rejects_network_file_db_and_trading_surfaces() -> None:
    source = Path(
        "src/polymarket_alpha_lab/"
        "market_research_inflation_breakeven_shift_digest.py",
    ).read_text()
    tree = ast.parse(source)
    lowered_source = source.lower()

    for forbidden in (
        "auth",
        "wallet",
        "place_order",
        "submit_order",
        "cancel_order",
        "replace_order",
        "exchange",
        "private_key",
        "api_key",
        "secret",
        "http",
        "socket",
        "subprocess",
        "open(",
        "pathlib",
    ):
        assert forbidden not in lowered_source

    banned_imports = {
        "requests",
        "httpx",
        "urllib",
        "socket",
        "websocket",
        "psycopg",
        "sqlite3",
        "sqlalchemy",
        "pathlib",
        "os",
        "subprocess",
    }
    banned_calls = {
        "open",
        "connect",
        "request",
        "urlopen",
        "get",
        "post",
        "put",
        "delete",
        "send",
        "submit",
        "cancel",
        "trade",
        "order",
        "wallet",
        "auth",
    }

    for node in ast.walk(tree):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            names = (
                [alias.name for alias in node.names]
                if isinstance(node, ast.Import)
                else [node.module or ""]
            )
            assert not any(name.split(".")[0] in banned_imports for name in names)
            if isinstance(node, ast.ImportFrom) and node.module == "dataclasses":
                assert all(alias.name != "asdict" for alias in node.names)
        if isinstance(node, ast.Call):
            if isinstance(node.func, ast.Name):
                assert node.func.id not in banned_calls
                assert node.func.id != "asdict"
            if isinstance(node.func, ast.Attribute):
                assert node.func.attr not in banned_calls
                assert node.func.attr != "asdict"
